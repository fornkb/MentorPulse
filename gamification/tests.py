from django.test import TestCase
from django.contrib.auth.models import User
from .models import Credit, CreditTransaction, Badge, UserBadge, LeaderboardEntry


class GamificationModelTests(TestCase):
    def test_user_creation_provisions_credits_and_transaction(self):
        """Registering a new user provisions 50 credits and a STARTING_BONUS transaction."""
        user = User.objects.create_user(username='gamified_user', password='password123')

        # Verify Credit model was created
        self.assertTrue(hasattr(user, 'credit'))
        self.assertEqual(user.credit.balance, 50)

        # Verify STARTING_BONUS transaction
        tx = CreditTransaction.objects.filter(user=user, reason='STARTING_BONUS').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 50)

    def test_badge_uniqueness(self):
        """User cannot earn the exact same badge more than once."""
        user = User.objects.create_user(username='badge_earner', password='password123')
        badge = Badge.objects.create(name='First Steps', description='Completed 1st mentorship')

        ub1 = UserBadge.objects.create(user=user, badge=badge)
        self.assertIsNotNone(ub1)

        with self.assertRaises(Exception):
            UserBadge.objects.create(user=user, badge=badge)
