from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Notification
from .services import send_notification
from .context_processors import unread_notifications


class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='alice', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

    def test_send_notification(self):
        notif = send_notification(
            user=self.user1,
            message="Test notification message",
            type="REQUEST_RECEIVED",
            link="/mentorships/"
        )
        self.assertEqual(notif.user, self.user1)
        self.assertEqual(notif.message, "Test notification message")
        self.assertEqual(notif.type, "REQUEST_RECEIVED")
        self.assertEqual(notif.link, "/mentorships/")
        self.assertFalse(notif.is_read)

    def test_notification_list_view(self):
        send_notification(self.user1, "Notif 1", "REQUEST_RECEIVED")
        send_notification(self.user1, "Notif 2", "SESSION_LOGGED")
        send_notification(self.user2, "Notif for Bob", "BADGE_EARNED")

        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notif 1")
        self.assertContains(response, "Notif 2")
        self.assertNotContains(response, "Notif for Bob")

    def test_notification_read_view(self):
        notif = send_notification(self.user1, "Click me", "BADGE_EARNED", link="/badges/")
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('notification_read', args=[notif.id]))
        self.assertRedirects(response, "/badges/")

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_read_view(self):
        send_notification(self.user1, "Notif 1", "REQUEST_RECEIVED")
        send_notification(self.user1, "Notif 2", "SESSION_LOGGED")
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('notification_mark_all_read'))
        self.assertRedirects(response, reverse('notifications_list'))

        self.assertEqual(self.user1.notifications.filter(is_read=False).count(), 0)

    def test_clear_read_notifications_view(self):
        n1 = send_notification(self.user1, "Read notif", "REQUEST_RECEIVED")
        n1.mark_as_read()
        send_notification(self.user1, "Unread notif", "SESSION_LOGGED")

        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('notification_clear_read'))
        self.assertRedirects(response, reverse('notifications_list'))

        self.assertEqual(self.user1.notifications.count(), 1)
        self.assertEqual(self.user1.notifications.first().message, "Unread notif")

    def test_unread_notifications_context_processor(self):
        send_notification(self.user1, "Notif 1", "REQUEST_RECEIVED")
        send_notification(self.user1, "Notif 2", "SESSION_LOGGED")

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user1

        context = unread_notifications(request)
        self.assertEqual(context['unread_notification_count'], 2)
        self.assertEqual(len(context['navbar_notifications']), 2)
