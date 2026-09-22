def unread_notifications(request):
    """
    Context processor to inject unread notification count and recent notifications
    into every template for authenticated users.
    """
    if request.user.is_authenticated:
        user_notifications = request.user.notifications.all()
        return {
            'unread_notification_count': user_notifications.filter(is_read=False).count(),
            'navbar_notifications': user_notifications[:5],
        }
    return {
        'unread_notification_count': 0,
        'navbar_notifications': [],
    }
