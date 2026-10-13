from io import StringIO
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from mentorship.models import Mentorship, Session
from .models import Notification, NotificationPreference
from .services import send_notification


class NotificationProductTests(TestCase):
    def setUp(self):
        self.mentor = User.objects.create_user('mentor')
        self.learner = User.objects.create_user('learner')
        self.mentorship = Mentorship.objects.create(mentor=self.mentor, learner=self.learner, status='ACTIVE', goals='Learn')
        self.session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()+timezone.timedelta(hours=2))
        self.client.force_login(self.learner)

    def test_reminders_are_sent_once_to_both_participants(self):
        for _ in range(2):
            call_command('send_session_reminders', stdout=StringIO())
        self.assertEqual(Notification.objects.filter(type='SESSION_REMINDER').count(), 2)
        self.session.refresh_from_db()
        self.assertIsNotNone(self.session.reminder_sent_at)

    def test_disabled_reminder_preference_is_respected(self):
        NotificationPreference.objects.create(user=self.learner, session_reminders=False)
        call_command('send_session_reminders', stdout=StringIO())
        self.assertFalse(Notification.objects.filter(user=self.learner).exists())
        self.assertEqual(Notification.objects.filter(user=self.mentor).count(), 1)

    def test_cancelled_completed_and_distant_sessions_are_not_reminded(self):
        for changes in [{'is_cancelled': True}, {'is_completed': True}, {'date': timezone.now()+timezone.timedelta(days=2)}]:
            Session.objects.filter(pk=self.session.pk).update(is_completed=False, is_cancelled=False)
            Session.objects.filter(pk=self.session.pk).update(**changes)
            call_command('send_session_reminders', stdout=StringIO())
        self.assertFalse(Notification.objects.exists())

    def test_preferences_disable_optional_updates_but_keep_decisions(self):
        self.client.post(reverse('notification_preferences'), {})
        self.assertIsNone(send_notification(self.learner, 'A session update', 'SESSION_LOGGED'))
        self.assertIsNone(send_notification(self.learner, 'A new badge', 'BADGE_EARNED'))
        self.assertIsNotNone(send_notification(self.learner, 'Accepted', 'REQUEST_ACCEPTED'))

    def test_summary_only_counts_current_users_unread_items(self):
        send_notification(self.mentor, 'Mentor notification', 'REQUEST_ACCEPTED')
        send_notification(self.learner, 'Learner notification', 'REQUEST_ACCEPTED')
        self.assertEqual(self.client.get(reverse('notification_summary')).json(), {'unread_count': 1})
        self.client.logout()
        self.assertEqual(self.client.get(reverse('notification_summary')).status_code, 302)

    def test_inbox_clear_and_mark_require_post(self):
        for name in ['notification_clear_read', 'notification_mark_all_read']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 405)

    def test_event_keys_make_notification_delivery_idempotent(self):
        for _ in range(2):
            send_notification(self.learner, 'Reminder', 'SESSION_REMINDER', event_key='same-event')
        self.assertEqual(Notification.objects.count(), 1)

    @override_settings(DEBUG=True)
    def test_reminder_server_includes_static_file_handling(self):
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from .management.commands.runserver_with_reminders import Command
        handler = Command().get_handler(use_static_handler=True, insecure_serving=False)
        self.assertIsInstance(handler, StaticFilesHandler)
