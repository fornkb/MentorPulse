from django.contrib.auth.models import User
from .models import Notification, NotificationPreference


def send_notification(user: User, message: str, type: str, link: str = "", event_key=None):
    """
    Central helper utility to create in-app notifications for users.
    
    Args:
        user: Target recipient (User instance)
        message: Notification text (max 255 chars)
        type: One of Notification.TYPE_CHOICES keys
        link: Optional redirect URL or route path
    """
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    category = {'SESSION_LOGGED': 'session_updates', 'SESSION_REMINDER': 'session_reminders',
                'DISCUSSION': 'discussions', 'BADGE_EARNED': 'achievements'}.get(type)
    if category and not getattr(preference, category):
        return None
    values = dict(
        user=user,
        message=message[:255],
        type=type,
        link=link or ""
    )
    if event_key:
        return Notification.objects.get_or_create(event_key=event_key, defaults=values)[0]
    return Notification.objects.create(**values)
