from django.db import models
from django.contrib.auth.models import User
from mentorship.models import Mentorship


class Credit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit')
    balance = models.IntegerField(default=50)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.balance} Credits"


class CreditTransaction(models.Model):
    REASON_CHOICES = [
        ('STARTING_BONUS', 'Starting Welcome Bonus'),
        ('SESSION_REQUEST', 'Mentorship Request Fee'),
        ('SESSION_REFUND', 'Mentorship Request Refund'),
        ('SESSION_COMPLETED_REWARD', 'Completed Session Reward'),
        ('PRIORITY_UNLOCK', 'Priority Queue Placement Fee'),
        ('ADMIN_ADJUSTMENT', 'Staff Balance Adjustment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    amount = models.IntegerField(help_text="Positive for earned, negative for spent")
    reason = models.CharField(max_length=40, choices=REASON_CHOICES)
    context = models.CharField(max_length=255, blank=True, help_text="Optional detail or mentorship reference")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{self.user.username}: {sign}{self.amount} ({self.reason})"


class Feedback(models.Model):
    RATING_CHOICES = [
        (5, '5 - Exceptional'),
        (4, '4 - Very Good'),
        (3, '3 - Good / Satisfactory'),
        (2, '2 - Needs Improvement'),
        (1, '1 - Unsatisfactory'),
    ]

    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='feedbacks')
    given_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_given')
    given_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks_received')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.given_by.username} rated {self.given_to.username}: {self.rating} stars"


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='bi-award-fill', help_text="Bootstrap icon class")
    category = models.CharField(max_length=50, default='General')

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awardees')
    earned_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_date']

    def __str__(self):
        return f"{self.user.username} unlocked {self.badge.name}"


class LeaderboardEntry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard_entry')
    score = models.FloatField(default=0.0)
    rank = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank', '-score']

    def __str__(self):
        return f"#{self.rank} {self.user.username} ({self.score:.1f} pts)"
