from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('REQUEST_RECEIVED', 'Mentorship Request Received'),
        ('REQUEST_ACCEPTED', 'Mentorship Request Accepted'),
        ('REQUEST_REJECTED', 'Mentorship Request Declined'),
        ('SESSION_LOGGED', 'Session Scheduled / Updated'),
        ('FEEDBACK_RECEIVED', 'Feedback Received'),
        ('BADGE_EARNED', 'Badge Awarded'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Recipient of the notification"
    )
    message = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, help_text="Target URL or path for interaction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"[{self.type}] to {self.user.username}: {self.message[:30]}... ({status})"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def get_icon(self):
        """Return icon class appropriate for the notification type."""
        icons = {
            'REQUEST_RECEIVED': 'bi-inbox-fill text-warning',
            'REQUEST_ACCEPTED': 'bi-check-circle-fill text-success',
            'REQUEST_REJECTED': 'bi-x-circle-fill text-danger',
            'SESSION_LOGGED': 'bi-calendar-event-fill text-info',
            'FEEDBACK_RECEIVED': 'bi-star-fill text-warning',
            'BADGE_EARNED': 'bi-award-fill text-purple',
        }
        return icons.get(self.type, 'bi-bell-fill text-primary')

    def get_badge_class(self):
        """Return badge style class based on notification type."""
        badges = {
            'REQUEST_RECEIVED': 'bg-warning text-dark',
            'REQUEST_ACCEPTED': 'bg-success text-light',
            'REQUEST_REJECTED': 'bg-danger text-light',
            'SESSION_LOGGED': 'bg-info text-dark',
            'FEEDBACK_RECEIVED': 'bg-warning text-dark',
            'BADGE_EARNED': 'bg-primary text-light',
        }
        return badges.get(self.type, 'bg-secondary text-light')
