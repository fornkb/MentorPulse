from django.contrib.auth.models import User
from .models import Notification


def send_notification(user: User, message: str, type: str, link: str = "") -> Notification:
    """
    Central helper utility to create in-app notifications for users.
    
    Args:
        user: Target recipient (User instance)
        message: Notification text (max 255 chars)
        type: One of Notification.TYPE_CHOICES keys
        link: Optional redirect URL or route path
    """
    return Notification.objects.create(
        user=user,
        message=message,
        type=type,
        link=link or ""
    )
