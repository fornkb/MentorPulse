from datetime import timedelta
from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from mentorship.models import Session
from notifications.services import send_notification


class Command(BaseCommand):
    help = 'Send upcoming-session inbox reminders. Safe to run repeatedly (schedule hourly).'

    def handle(self, *args, **options):
        now = timezone.now()
        count = 0
        ids = Session.objects.filter(date__gt=now, date__lte=now + timedelta(hours=24),
            is_completed=False, is_cancelled=False, reminder_sent_at__isnull=True,
            mentorship__status='ACTIVE').values_list('pk', flat=True)
        for pk in ids:
            with transaction.atomic():
                claimed = Session.objects.filter(pk=pk, reminder_sent_at__isnull=True,
                    is_completed=False, is_cancelled=False, mentorship__status='ACTIVE',
                    date__gt=now, date__lte=now + timedelta(hours=24)).update(reminder_sent_at=now)
                if not claimed:
                    continue
                session = Session.objects.select_related('mentorship__mentor__profile', 'mentorship__learner__profile').get(pk=pk)
                for user in [session.mentorship.mentor, session.mentorship.learner]:
                    local = timezone.localtime(session.date, ZoneInfo(user.profile.timezone))
                    notification = send_notification(user,
                        f'Reminder: your session starts {local:%b %d at %H:%M} ({user.profile.timezone}).',
                        'SESSION_REMINDER', reverse('mentorship_workspace', args=[session.mentorship_id]),
                        event_key=f'reminder:{pk}:{session.date.isoformat()}:{user.pk}')
                    count += notification is not None
        self.stdout.write(self.style.SUCCESS(f'{count} reminders sent.'))
