from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification


@login_required
def notification_list_view(request):
    """Full notifications inbox view with tabbed filtering."""
    tab = request.GET.get('tab', 'all')
    user_notifications = request.user.notifications.all()

    unread_count = user_notifications.filter(is_read=False).count()
    total_count = user_notifications.count()

    if tab == 'unread':
        notifications = user_notifications.filter(is_read=False)
    else:
        notifications = user_notifications

    context = {
        'notifications': notifications,
        'active_tab': tab,
        'unread_count': unread_count,
        'total_count': total_count,
    }
    return render(request, 'notifications/list.html', context)


@login_required
def notification_read_view(request, notification_id):
    """Mark a specific notification as read and route directly to its destination link."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications_list')


@login_required
def mark_all_read_view(request):
    """Mark all unread notifications as read for current user."""
    updated = request.user.notifications.filter(is_read=False).update(is_read=True)
    if updated > 0:
        messages.success(request, f"Marked {updated} notification{'s' if updated != 1 else ''} as read.")
    else:
        messages.info(request, "No unread notifications to mark.")

    referer = request.META.get('HTTP_REFERER')
    if referer and '/notifications/' in referer:
        return redirect(referer)
    return redirect('notifications_list')


@login_required
def clear_read_notifications_view(request):
    """Delete read notifications to tidy the inbox."""
    deleted, _ = request.user.notifications.filter(is_read=True).delete()
    if deleted > 0:
        messages.info(request, f"Cleared {deleted} read notification{'s' if deleted != 1 else ''}.")
    else:
        messages.info(request, "No read notifications found to clear.")

    return redirect('notifications_list')
