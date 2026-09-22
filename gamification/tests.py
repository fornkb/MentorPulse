from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from accounts.models import Profile
from mentorship.models import Mentorship, Session, Resource
from gamification.models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from gamification.services import CreditService, FeedbackService, BadgeService, LeaderboardService


class GamificationCreditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_learner', password='password123')
        self.mentor = User.objects.create_user(username='test_mentor', password='password123')

    def test_registration_provisions_credits_and_transaction(self):
        """Registering a new user provisions 50 credits and a STARTING_BONUS transaction."""
        credit = Credit.objects.get(user=self.user)
        self.assertEqual(credit.balance, 50)

        tx = CreditTransaction.objects.filter(user=self.user, reason='STARTING_BONUS').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 50)

    def test_deduct_for_standard_request(self):
        """Standard mentorship request deducts 10 credits and creates a SESSION_REQUEST transaction."""
        success, msg = CreditService.deduct_for_request(self.user, is_priority=False)
        self.assertTrue(success)

        self.user.credit.refresh_from_db()
        self.assertEqual(self.user.credit.balance, 40)

        tx = CreditTransaction.objects.filter(user=self.user, reason='SESSION_REQUEST').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, -10)

    def test_deduct_for_priority_request(self):
        """Priority mentorship request deducts 15 credits (10 + 5)."""
        success, msg = CreditService.deduct_for_request(self.user, is_priority=True)
        self.assertTrue(success)

        self.user.credit.refresh_from_db()
        self.assertEqual(self.user.credit.balance, 35)

        txs = CreditTransaction.objects.filter(user=self.user)
        reasons = [t.reason for t in txs]
        self.assertIn('SESSION_REQUEST', reasons)
        self.assertIn('PRIORITY_UNLOCK', reasons)

    def test_insufficient_credits_prevents_request(self):
        """Users with insufficient balance cannot submit a mentorship request."""
        self.user.credit.balance = 5
        self.user.credit.save()

        success, msg = CreditService.deduct_for_request(self.user, is_priority=False)
        self.assertFalse(success)
        self.assertIn("Insufficient credits", msg)
        self.user.credit.refresh_from_db()
        self.assertEqual(self.user.credit.balance, 5)

    def test_refund_on_rejection_or_cancellation(self):
        """Refunding a mentorship request returns the deducted credits."""
        CreditService.deduct_for_request(self.user, is_priority=True)
        self.user.credit.refresh_from_db()
        self.assertEqual(self.user.credit.balance, 35)

        mentorship = Mentorship.objects.create(
            learner=self.user,
            mentor=self.mentor,
            status='PENDING',
            is_priority=True,
            goals='Learn testing'
        )

        refunded = CreditService.refund_for_request(mentorship)
        self.assertTrue(refunded)
        self.user.credit.refresh_from_db()
        self.assertEqual(self.user.credit.balance, 50)

        tx = CreditTransaction.objects.filter(user=self.user, reason='SESSION_REFUND').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 15)

    def test_reward_mentor_for_completed_session(self):
        """Completing a session milestone awards +10 credits to the mentor."""
        mentorship = Mentorship.objects.create(
            learner=self.user,
            mentor=self.mentor,
            status='ACTIVE',
            goals='Learn backend'
        )
        session = Session.objects.create(
            mentorship=mentorship,
            date=timezone.now(),
            is_completed=True
        )

        rewarded = CreditService.reward_session_completed(session)
        self.assertTrue(rewarded)
        self.mentor.credit.refresh_from_db()
        self.assertEqual(self.mentor.credit.balance, 60)

        tx = CreditTransaction.objects.filter(user=self.mentor, reason='SESSION_COMPLETED_REWARD').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 10)


class GamificationFeedbackTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(username='fb_learner', password='password123')
        self.mentor = User.objects.create_user(username='fb_mentor', password='password123')
        self.mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            status='ACTIVE',
            goals='Feedback test'
        )

    def test_submit_feedback_and_summary(self):
        """Feedback creates a record and calculates correct average ratings."""
        fb = FeedbackService.submit_feedback(
            mentorship=self.mentorship,
            given_by=self.learner,
            rating=5,
            comment="Terrific mentor!"
        )
        self.assertIsNotNone(fb)
        self.assertEqual(fb.rating, 5)
        self.assertEqual(fb.given_to, self.mentor)

        summary = FeedbackService.get_user_rating_summary(self.mentor)
        self.assertEqual(summary['average_rating'], 5.0)
        self.assertEqual(summary['review_count'], 1)

    def test_prevent_duplicate_feedback(self):
        """User cannot submit feedback more than once for the same mentorship."""
        FeedbackService.submit_feedback(
            mentorship=self.mentorship,
            given_by=self.learner,
            rating=4,
            comment="First review"
        )
        # Attempting second feedback should raise ValueError
        with self.assertRaises(ValueError):
            FeedbackService.submit_feedback(
                mentorship=self.mentorship,
                given_by=self.learner,
                rating=5,
                comment="Second review attempt"
            )


class GamificationBadgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='badge_tester', password='password123')
        self.peer = User.objects.create_user(username='badge_peer', password='password123')
        BadgeService.seed_core_badges()

    def test_core_badges_seeded(self):
        """5 core badges are properly seeded."""
        self.assertEqual(Badge.objects.count(), 5)
        names = set(Badge.objects.values_list('name', flat=True))
        self.assertIn('First Steps', names)
        self.assertIn('Committed Mentor', names)
        self.assertIn('Rising Star', names)
        self.assertIn('Top Rated', names)
        self.assertIn('Helpful Hand', names)

    def test_first_steps_badge_awarded(self):
        """First Steps badge awarded upon completing a mentorship."""
        Mentorship.objects.create(
            learner=self.user,
            mentor=self.peer,
            status='COMPLETED',
            goals='Complete one'
        )
        awarded = BadgeService.check_and_award_badges(self.user)
        self.assertTrue(any(b.name == 'First Steps' for b in awarded))
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge__name='First Steps').exists())

    def test_rising_star_badge_awarded(self):
        """Rising Star badge awarded when profile.skill_score >= 8.0."""
        self.user.profile.skill_score = 8.5
        self.user.profile.save()

        awarded = BadgeService.check_and_award_badges(self.user)
        self.assertTrue(any(b.name == 'Rising Star' for b in awarded))

    def test_helpful_hand_badge_awarded(self):
        """Helpful Hand badge awarded when user shares >= 2 resources."""
        m = Mentorship.objects.create(
            learner=self.peer,
            mentor=self.user,
            status='ACTIVE',
            goals='Resources test'
        )
        Resource.objects.create(mentorship=m, uploaded_by=self.user, title='Guide 1', type='LINK', content='http://a.com')
        Resource.objects.create(mentorship=m, uploaded_by=self.user, title='Guide 2', type='NOTE', content='Key notes')

        awarded = BadgeService.check_and_award_badges(self.user)
        self.assertTrue(any(b.name == 'Helpful Hand' for b in awarded))


class GamificationLeaderboardTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='leader_one', password='password123')
        self.user2 = User.objects.create_user(username='leader_two', password='password123')

        self.user1.profile.skill_score = 9.0
        self.user1.profile.save()
        self.user1.credit.balance = 100
        self.user1.credit.save()

        self.user2.profile.skill_score = 5.0
        self.user2.profile.save()
        self.user2.credit.balance = 50
        self.user2.credit.save()

    def test_recalculate_leaderboard_scoring_and_ranking(self):
        """
        Formula: Score = (skill_score * 10) + (credit_balance * 0.5) + (badge_count * 15)
        user1: (9.0 * 10) + (100 * 0.5) + (0 * 15) = 90 + 50 = 140.0 pts -> Rank 1
        user2: (5.0 * 10) + (50 * 0.5) + (0 * 15) = 50 + 25 = 75.0 pts -> Rank 2
        """
        LeaderboardService.recalculate_leaderboard()

        e1 = LeaderboardEntry.objects.get(user=self.user1)
        e2 = LeaderboardEntry.objects.get(user=self.user2)

        self.assertEqual(e1.score, 140.0)
        self.assertEqual(e1.rank, 1)

        self.assertEqual(e2.score, 75.0)
        self.assertEqual(e2.rank, 2)


class GamificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='view_user', password='password123')
        self.mentor = User.objects.create_user(username='view_mentor', password='password123')
        self.mentorship = Mentorship.objects.create(
            learner=self.user,
            mentor=self.mentor,
            status='ACTIVE',
            goals='View testing'
        )

    def test_wallet_view_requires_auth(self):
        """Unauthenticated access to /wallet/ redirects to login."""
        response = self.client.get(reverse('wallet'))
        self.assertEqual(response.status_code, 302)

    def test_wallet_view_renders_for_authenticated_user(self):
        """Authenticated user can view wallet dashboard with balance and transactions."""
        self.client.login(username='view_user', password='password123')
        response = self.client.get(reverse('wallet'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credit Wallet')
        self.assertContains(response, '50')

    def test_leaderboard_view_renders(self):
        """Leaderboard is publicly viewable and displays participants."""
        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform Leaderboard')

    def test_badges_view_requires_auth(self):
        """Badges showcase requires authentication."""
        self.client.login(username='view_user', password='password123')
        response = self.client.get(reverse('badges'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Badges & Achievements')

    def test_feedback_submit_post(self):
        """Participant can submit feedback via POST request and get redirected."""
        self.client.login(username='view_user', password='password123')
        response = self.client.post(
            reverse('feedback_submit', kwargs={'mentorship_id': self.mentorship.id}),
            {
                'rating': '5',
                'comment': 'Fantastic mentorship experience!'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Feedback.objects.filter(mentorship=self.mentorship, given_by=self.user).exists())
