from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import Avg, Q, F
from django.utils import timezone
from django.urls import reverse
from .models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from mentorship.models import Mentorship, Resource
from notifications.services import send_notification
from mentorpulse.db import retry_database_lock


class CreditService:
    @staticmethod
    def get_or_create_credit(user):
        with transaction.atomic():
            credit, created = Credit.objects.get_or_create(user=user, defaults={'balance': 50})
            if created:
                CreditTransaction.objects.create(user=user, amount=50, reason='STARTING_BONUS',
                    context='Welcome credit bonus upon registration', event_key=f'welcome:{user.pk}')
            return credit

    @staticmethod
    @retry_database_lock
    def deduct_for_request(learner, is_priority=False, mentorship=None):
        with transaction.atomic():
            credit = CreditService.get_or_create_credit(learner)
            cost = 15 if is_priority else 10
            # The conditional database update serializes spenders even on SQLite.
            changed = Credit.objects.filter(pk=credit.pk, balance__gte=cost).update(
                balance=F('balance') - cost, updated_at=timezone.now())
            if not changed:
                credit.refresh_from_db()
                return False, f'Insufficient credits ({credit.balance} available). You need {cost} credits.'
            CreditTransaction.objects.create(user=learner, amount=-10, reason='SESSION_REQUEST',
                context='Mentorship application request fee',
                event_key=f'request:{mentorship.pk}' if mentorship else None)
            if is_priority:
                CreditTransaction.objects.create(user=learner, amount=-5, reason='PRIORITY_UNLOCK',
                    context='Priority queue placement fee',
                    event_key=f'priority:{mentorship.pk}' if mentorship else None)
            return True, f'Deducted {cost} credits.'

    @staticmethod
    @retry_database_lock
    def _award(user, amount, reason, context, event_key):
        try:
            with transaction.atomic():
                credit = CreditService.get_or_create_credit(user)
                # Unique event keys make retries safe; the balance and ledger commit together.
                if CreditTransaction.objects.filter(user=user, context=context, reason=reason).exists():
                    return False
                CreditTransaction.objects.create(user=user, amount=amount, reason=reason,
                    context=context, event_key=event_key)
                Credit.objects.filter(pk=credit.pk).update(balance=F('balance') + amount, updated_at=timezone.now())
            return True
        except IntegrityError:
            if CreditTransaction.objects.filter(event_key=event_key).exists():
                return False
            raise

    @staticmethod
    def refund_for_request(mentorship):
        return CreditService._award(mentorship.learner, 15 if mentorship.is_priority else 10,
            'SESSION_REFUND', f'Refund for mentorship #{mentorship.pk}', f'refund:{mentorship.pk}')

    @staticmethod
    def reward_mentor_for_session(session):
        if not session.is_completed or session.is_cancelled:
            return False
        awarded = CreditService._award(session.mentorship.mentor, 10, 'SESSION_COMPLETED_REWARD',
            f'Completed meeting session #{session.pk}', f'session:{session.pk}')
        if awarded:
            BadgeService.check_and_award_badges(session.mentorship.mentor)
        return awarded

    reward_session_completed = reward_mentor_for_session


class FeedbackService:
    @staticmethod
    @transaction.atomic
    def submit_feedback(mentorship: Mentorship, given_by: User, rating: int, comment: str) -> Feedback:
        """
        Save collaboration rating and review, then trigger badge and ranking recalculation.
        """
        if given_by.pk not in [mentorship.mentor_id, mentorship.learner_id] or mentorship.status not in ['ACTIVE', 'COMPLETED']:
            raise ValueError('Only active or completed mentorship participants may leave feedback.')
        if rating not in range(1, 6):
            raise ValueError('Choose a rating between 1 and 5.')
        if mentorship.feedbacks.filter(given_by=given_by).exists():
            raise ValueError("Feedback already submitted for this mentorship.")

        given_to = mentorship.mentor if given_by == mentorship.learner else mentorship.learner

        feedback = Feedback.objects.create(
            mentorship=mentorship,
            given_by=given_by,
            given_to=given_to,
            rating=rating,
            comment=comment
        )

        send_notification(
            user=given_to,
            message=f"You received a {rating}-star rating and review from {given_by.get_full_name() or given_by.username}!",
            type='FEEDBACK_RECEIVED',
            link=reverse('mentorship_workspace', args=[mentorship.id])
        )

        # Check badges for review recipient and giver
        BadgeService.check_and_award_badges(given_to)
        BadgeService.check_and_award_badges(given_by)
        LeaderboardService.recalculate_leaderboard()
        return feedback

    @staticmethod
    def get_user_rating_summary(user: User) -> dict:
        """Calculate average star rating and review count for a user."""
        reviews = Feedback.objects.filter(given_to=user)
        count = reviews.count()
        if count == 0:
            return {
                'average_rating': 0.0,
                'review_count': 0,
                'reviews': []
            }

        avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0
        return {
            'average_rating': round(avg, 1),
            'review_count': count,
            'reviews': reviews[:5]
        }


class BadgeService:
    CORE_BADGES = [
        {
            'name': 'First Steps',
            'description': 'Successfully completed your first collaborative mentorship milestone on MentorPulse.',
            'icon': 'bi-mortarboard-fill',
            'category': 'Milestone'
        },
        {
            'name': 'Committed Mentor',
            'description': 'Guided peers through 2 or more fully completed mentorship roadmaps.',
            'icon': 'bi-award-fill',
            'category': 'Mentorship'
        },
        {
            'name': 'Rising Star',
            'description': 'Achieved an exemplary platform Skill Score rating of 8.0 or higher.',
            'icon': 'bi-stars',
            'category': 'Expertise'
        },
        {
            'name': 'Top Rated',
            'description': 'Maintained a stellar 4.5+ star peer review rating across collaborations.',
            'icon': 'bi-heart-fill',
            'category': 'Reputation'
        },
        {
            'name': 'Helpful Hand',
            'description': 'Shared 2 or more learning resources (links, guides, or files) with peers.',
            'icon': 'bi-folder-check',
            'category': 'Community'
        },
    ]

    @staticmethod
    def seed_core_badges():
        """Ensure core badge definitions exist in the database."""
        for bdata in BadgeService.CORE_BADGES:
            Badge.objects.get_or_create(
                name=bdata['name'],
                defaults={
                    'description': bdata['description'],
                    'icon': bdata['icon'],
                    'category': bdata['category']
                }
            )

    @staticmethod
    def check_and_award_badges(user: User) -> list[Badge]:
        """
        Evaluate criteria for all badges and auto-award unlocked ones.
        Returns list of newly awarded badges.
        """
        BadgeService.seed_core_badges()
        newly_awarded = []

        # 1. First Steps: Completed 1st mentorship
        has_completed_any = Mentorship.objects.filter(
            status='COMPLETED'
        ).filter(
            Q(learner=user) | Q(mentor=user)
        ).exists()
        if has_completed_any:
            b = Badge.objects.get(name='First Steps')
            _, created = UserBadge.objects.get_or_create(user=user, badge=b)
            if created:
                newly_awarded.append(b)

        # 2. Committed Mentor: Completed >= 2 mentorships as mentor
        mentor_completed_count = Mentorship.objects.filter(mentor=user, status='COMPLETED').count()
        if mentor_completed_count >= 2:
            b = Badge.objects.get(name='Committed Mentor')
            _, created = UserBadge.objects.get_or_create(user=user, badge=b)
            if created:
                newly_awarded.append(b)

        # 3. Rising Star: Skill score >= 8.0
        if hasattr(user, 'profile') and user.profile.skill_score >= 8.0:
            b = Badge.objects.get(name='Rising Star')
            _, created = UserBadge.objects.get_or_create(user=user, badge=b)
            if created:
                newly_awarded.append(b)

        # 4. Top Rated: Average rating >= 4.5 with >= 1 review
        summary = FeedbackService.get_user_rating_summary(user)
        if summary['review_count'] >= 1 and summary['average_rating'] >= 4.5:
            b = Badge.objects.get(name='Top Rated')
            _, created = UserBadge.objects.get_or_create(user=user, badge=b)
            if created:
                newly_awarded.append(b)

        # 5. Helpful Hand: Shared >= 2 resources
        resource_count = Resource.objects.filter(uploaded_by=user).count()
        if resource_count >= 2:
            b = Badge.objects.get(name='Helpful Hand')
            _, created = UserBadge.objects.get_or_create(user=user, badge=b)
            if created:
                newly_awarded.append(b)

        for b in newly_awarded:
            send_notification(
                user=user,
                message=f"🏆 Achievement Unlocked: You earned the '{b.name}' badge!",
                type='BADGE_EARNED',
                link=reverse('badges')
            )

        return newly_awarded


class LeaderboardService:
    @staticmethod
    def recalculate_leaderboard():
        """
        Recompute dynamic scores for all users and update ranks:
        Score = (skill_score * 10) + (credit_balance * 0.5) + (badge_count * 15)
        """
        users = User.objects.filter(is_active=True).select_related('profile', 'credit').prefetch_related('user_badges')
        scored_users = []

        for u in users:
            skill_score = u.profile.skill_score if hasattr(u, 'profile') else 0.0
            try:
                credit_balance = u.credit.balance
            except Exception:
                credit, _ = Credit.objects.get_or_create(user=u, defaults={'balance': 50})
                credit_balance = credit.balance

            badge_count = u.user_badges.count()

            # Composite Score calculation
            score = (skill_score * 10.0) + (credit_balance * 0.5) + (badge_count * 15.0)
            score = round(score, 1)

            scored_users.append((u, score))

        # Sort descending by composite score
        scored_users.sort(key=lambda item: item[1], reverse=True)

        # Assign consecutive ranks (1, 2, 3...)
        for rank_idx, (u, score) in enumerate(scored_users, start=1):
            entry, _ = LeaderboardEntry.objects.get_or_create(user=u)
            entry.score = score
            entry.rank = rank_idx
            entry.save()
