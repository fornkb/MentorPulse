from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from gamification.models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from gamification.services import CreditService, FeedbackService, BadgeService, LeaderboardService
from mentorship.models import Mentorship


class Command(BaseCommand):
    help = "Seed Phase 4 gamification data: credits, transactions, feedback reviews, badges, and leaderboard rankings"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Phase 4 Credit Economy, Feedback, Badges, and Leaderboard..."))

        # 1. Fetch test accounts
        try:
            alex = User.objects.get(username='alex_mentor')
            david = User.objects.get(username='david_frontend')
            maya = User.objects.get(username='maya_design')
            sara = User.objects.get(username='sara_learner')
            charlie = User.objects.get(username='charlie_dual')
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Error fetching users: {e}. Run seed_phase1 first."))
            return

        # 2. Seed / Ensure Core Badges
        BadgeService.seed_core_badges()
        self.stdout.write(self.style.SUCCESS("Core badges initialized: First Steps, Committed Mentor, Rising Star, Top Rated, Helpful Hand."))

        # 3. Seed Realistic Credit Wallets & Transaction Ledgers
        wallets_data = [
            {
                'user': alex,
                'balance': 85,
                'transactions': [
                    (50, 'STARTING_BONUS', 'Welcome credit bonus upon registration', 60),
                    (10, 'SESSION_COMPLETED_REWARD', 'Completed milestone reward with @charlie_dual', 40),
                    (15, 'SESSION_COMPLETED_REWARD', 'Mentorship roadmap completion reward with @charlie_dual', 20),
                    (10, 'SESSION_COMPLETED_REWARD', 'Active mentorship consultation bonus', 5),
                ]
            },
            {
                'user': david,
                'balance': 70,
                'transactions': [
                    (50, 'STARTING_BONUS', 'Welcome credit bonus upon registration', 45),
                    (10, 'SESSION_COMPLETED_REWARD', 'Component architecture session completed with @sara_learner', 7),
                    (10, 'SESSION_COMPLETED_REWARD', 'Storybook workflow milestone bonus', 3),
                ]
            },
            {
                'user': maya,
                'balance': 60,
                'transactions': [
                    (50, 'STARTING_BONUS', 'Welcome credit bonus upon registration', 30),
                    (10, 'SESSION_COMPLETED_REWARD', 'Design critique session reward', 10),
                ]
            },
            {
                'user': charlie,
                'balance': 40,
                'transactions': [
                    (50, 'STARTING_BONUS', 'Welcome credit bonus upon registration', 60),
                    (-10, 'SESSION_REQUEST', 'Mentorship booking fee for @alex_mentor', 55),
                ]
            },
            {
                'user': sara,
                'balance': 25,
                'transactions': [
                    (50, 'STARTING_BONUS', 'Welcome credit bonus upon registration', 20),
                    (-10, 'SESSION_REQUEST', 'Mentorship booking fee for @david_frontend', 14),
                    (-5, 'PRIORITY_UNLOCK', '⭐ Fast-track priority queue unlock for @david_frontend', 14),
                    (-10, 'SESSION_REQUEST', 'Mentorship booking fee for @maya_design', 1),
                ]
            },
        ]

        for w in wallets_data:
            u = w['user']
            credit, _ = Credit.objects.get_or_create(user=u)
            credit.balance = w['balance']
            credit.save()

            # Clean and recreate demo transactions
            u.credit_transactions.all().delete()
            for amount, reason, context, days_ago in w['transactions']:
                tx = CreditTransaction.objects.create(
                    user=u,
                    amount=amount,
                    reason=reason,
                    context=context
                )
                if days_ago:
                    CreditTransaction.objects.filter(id=tx.id).update(
                        created_at=timezone.now() - timedelta(days=days_ago)
                    )

        self.stdout.write(self.style.SUCCESS("Credit balances and transaction ledgers seeded."))

        # 4. Seed Peer Reviews & Feedback
        # Fetch mentorships
        m_completed = Mentorship.objects.filter(status='COMPLETED', learner=charlie, mentor=alex).first()
        m_active = Mentorship.objects.filter(learner=sara, mentor=david).first()

        if m_completed:
            Feedback.objects.filter(mentorship=m_completed).delete()
            Feedback.objects.create(
                mentorship=m_completed,
                given_by=charlie,
                given_to=alex,
                rating=5,
                comment="Alex is an exceptional systems mentor. He guided me through distributed task queues, database concurrency, and container deployment. His deep code reviews dramatically leveled up my backend engineering skills!",
            )
            Feedback.objects.create(
                mentorship=m_completed,
                given_by=alex,
                given_to=charlie,
                rating=5,
                comment="Charlie is a remarkably diligent engineer. He arrived at every session thoroughly prepared with great questions and implemented feedback with high craftsmanship.",
            )
            self.stdout.write(self.style.SUCCESS("Seeded 5-star reviews for completed mentorship (Charlie & Alex)."))

        if m_active:
            Feedback.objects.filter(mentorship=m_active).delete()
            Feedback.objects.create(
                mentorship=m_active,
                given_by=sara,
                given_to=david,
                rating=5,
                comment="David's guidance on modern React architecture and design tokens has been game-changing for my frontend confidence. Highly recommended!",
            )
            self.stdout.write(self.style.SUCCESS("Seeded review for active mentorship (Sara -> David)."))

        # 5. Check and Award Badges for all users
        for u in [alex, david, maya, sara, charlie]:
            BadgeService.check_and_award_badges(u)

        # Ensure showcase badges for demo polish
        badge_top_rated = Badge.objects.get(name='Top Rated')
        badge_rising_star = Badge.objects.get(name='Rising Star')
        badge_committed = Badge.objects.get(name='Committed Mentor')
        badge_first_steps = Badge.objects.get(name='First Steps')
        badge_helpful = Badge.objects.get(name='Helpful Hand')

        UserBadge.objects.get_or_create(user=alex, badge=badge_top_rated)
        UserBadge.objects.get_or_create(user=alex, badge=badge_rising_star)
        UserBadge.objects.get_or_create(user=alex, badge=badge_committed)
        UserBadge.objects.get_or_create(user=alex, badge=badge_first_steps)

        UserBadge.objects.get_or_create(user=david, badge=badge_helpful)
        UserBadge.objects.get_or_create(user=david, badge=badge_rising_star)
        UserBadge.objects.get_or_create(user=david, badge=badge_first_steps)

        UserBadge.objects.get_or_create(user=charlie, badge=badge_first_steps)
        UserBadge.objects.get_or_create(user=sara, badge=badge_first_steps)

        self.stdout.write(self.style.SUCCESS("Badges checked and assigned to demo accounts."))

        # Ensure any existing users also have credits
        for u in User.objects.all():
            Credit.objects.get_or_create(user=u, defaults={'balance': 50})

        # 6. Recalculate platform leaderboard
        LeaderboardService.recalculate_leaderboard()
        self.stdout.write(self.style.SUCCESS("Leaderboard recalculated with composite scoring formula."))

        # Print top 5 leaderboard entries
        self.stdout.write("\n" + "="*50)
        self.stdout.write("PLATFORM LEADERBOARD STANDINGS:")
        self.stdout.write("="*50)
        for entry in LeaderboardEntry.objects.all().order_by('rank')[:5]:
            bal = entry.user.credit.balance if hasattr(entry.user, 'credit') else 50
            badges = entry.user.user_badges.count()
            self.stdout.write(f"#{entry.rank}: @{entry.user.username} - {entry.score} pts (Credits: {bal}, Badges: {badges})")
        self.stdout.write("="*50 + "\n")

        self.stdout.write(self.style.SUCCESS("Phase 4 seeding completed successfully!"))
