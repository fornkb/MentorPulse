from django.contrib.auth.models import User
from django.db.models import Avg, Q
from django.utils import timezone
from .models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from mentorship.models import Mentorship, Resource


class CreditService:
    @staticmethod
    def get_or_create_credit(user: User) -> Credit:
        """Ensure user has a Credit wallet record with starting bonus."""
        credit, created = Credit.objects.get_or_create(user=user, defaults={'balance': 50})
        if created:
            CreditTransaction.objects.create(
                user=user,
                amount=50,
                reason='STARTING_BONUS',
                context='Welcome credit bonus upon registration'
            )
        return credit

    @staticmethod
    def deduct_for_request(learner: User, is_priority: bool = False) -> tuple[bool, str]:
        """
        Deduct credits for initiating a mentorship request.
        Standard Fee: 10 credits.
        Priority Fee: 15 credits (10 + 5 priority queue placement).
        """
        credit = CreditService.get_or_create_credit(learner)
        required_credits = 15 if is_priority else 10

        if credit.balance < required_credits:
            return (
                False,
                f"Insufficient credits ({credit.balance} available). You need at least {required_credits} credits to submit this request."
            )

        # 1. Deduct standard request fee
        credit.balance -= 10
        CreditTransaction.objects.create(
            user=learner,
            amount=-10,
            reason='SESSION_REQUEST',
            context='Mentorship application request fee'
        )

        # 2. Deduct priority fee if selected
        if is_priority:
            credit.balance -= 5
            CreditTransaction.objects.create(
                user=learner,
                amount=-5,
                reason='PRIORITY_UNLOCK',
                context='⭐ Fast-track priority queue unlock'
            )

        credit.save()
        LeaderboardService.recalculate_leaderboard()
        return (True, f"Deducted {required_credits} credits successfully.")

    @staticmethod
    def refund_for_request(mentorship: Mentorship) -> bool:
        """
        Refund credits when a mentorship request is rejected or cancelled.
        """
        learner = mentorship.learner
        credit = CreditService.get_or_create_credit(learner)

        refund_amount = 15 if mentorship.is_priority else 10

        # Check if already refunded to prevent double refunds
        context_check = f"Refund for mentorship #{mentorship.id}"
        if CreditTransaction.objects.filter(user=learner, context=context_check).exists():
            return False

        credit.balance += refund_amount
        credit.save()

        CreditTransaction.objects.create(
            user=learner,
            amount=refund_amount,
            reason='SESSION_REFUND',
            context=context_check
        )
        LeaderboardService.recalculate_leaderboard()
        return True

    @staticmethod
    def reward_mentor_for_session(session) -> bool:
        """
        Award mentor +10 credits for completing a meeting session.
        """
        mentor = session.mentorship.mentor
        credit = CreditService.get_or_create_credit(mentor)

        context_label = f"Completed meeting session #{session.id}"
        # Prevent duplicate rewards for the same session
        if CreditTransaction.objects.filter(user=mentor, context=context_label).exists():
            return False

        credit.balance += 10
        credit.save()

        CreditTransaction.objects.create(
            user=mentor,
            amount=10,
            reason='SESSION_COMPLETED_REWARD',
            context=context_label
        )

        # Check badges & leaderboard
        BadgeService.check_and_award_badges(mentor)
        LeaderboardService.recalculate_leaderboard()
        return True

    reward_session_completed = reward_mentor_for_session


class FeedbackService:
    @staticmethod
    def submit_feedback(mentorship: Mentorship, given_by: User, rating: int, comment: str) -> Feedback:
        """
        Save collaboration rating and review, then trigger badge and ranking recalculation.
        """
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
