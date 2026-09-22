from django.conf import settings
from django.contrib.auth.models import User


def demo_accounts(request):
    """
    Context processor to provide demo user accounts for the instant 1-click
    role switcher in the navigation bar when DEBUG=True.
    """
    if not settings.DEBUG:
        return {'is_debug': False, 'demo_users_by_role': {}}

    active_users = User.objects.filter(is_active=True).select_related('profile').prefetch_related('role_assignments').order_by('id')

    admins = []
    mentors = []
    learners = []
    others = []

    for u in active_users:
        if u.is_superuser or u.is_staff:
            admins.append(u)
        elif hasattr(u, 'profile') and u.profile.is_mentor:
            mentors.append(u)
        elif hasattr(u, 'profile') and u.profile.is_learner:
            learners.append(u)
        else:
            others.append(u)

    return {
        'is_debug': settings.DEBUG,
        'demo_users_by_role': {
            'admins': admins,
            'mentors': mentors,
            'learners': learners,
            'others': others,
        },
    }
