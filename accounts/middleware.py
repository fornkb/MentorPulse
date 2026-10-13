from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.utils import timezone


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.deactivate()
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            try:
                timezone.activate(ZoneInfo(request.user.profile.timezone))
            except ZoneInfoNotFoundError:
                pass
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
