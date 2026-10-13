import re
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core import mail, signing
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import RoleAssignment, Skill, SavedMentor, UserReport, AvailabilitySlot
from .views import send_verification_email
from matching.services import calculate_match_score
from mentorship.models import Mentorship, Progress, Session, Milestone


class AccountProductTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('learner', email='learner@example.com', password='Pass123!')
        self.mentor = User.objects.create_user('mentor', password='Pass123!')
        RoleAssignment.objects.create(user=self.mentor, role='Mentor')
        self.client.force_login(self.user)

    def test_all_account_pages_render(self):
        for name in ['account_settings', 'profile_edit', 'notification_preferences', 'password_change', 'password_reset']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse('report_user', args=[self.mentor.pk])).status_code, 200)
        self.client.force_login(self.mentor)
        for name in ['availability_settings', 'mentor_verification_request']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_email_verification_token_is_bound_to_current_email(self):
        send_verification_email(self.user)
        token = re.search(r'verify-email/([^/]+)/', mail.outbox[0].body).group(1)
        self.user.email = 'changed@example.com'
        self.user.save()
        self.assertEqual(self.client.get(reverse('verify_email', args=[token])).status_code, 400)
        self.assertFalse(type(self.user.profile).objects.get(user=self.user).email_verified)

    def test_valid_verification_sets_flag_without_logging_in(self):
        token = signing.dumps({'user': self.user.pk, 'email': self.user.email}, salt='email-verification')
        self.client.logout()
        self.assertEqual(self.client.get(reverse('verify_email', args=[token])).status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_verified)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_expired_verification_is_rejected(self):
        token = signing.dumps({'user': self.user.pk, 'email': self.user.email}, salt='email-verification')
        with patch('django.core.signing.time.time', return_value=timezone.now().timestamp()+86402):
            self.assertEqual(self.client.get(reverse('verify_email', args=[token])).status_code, 400)

    def test_resend_cooldown_prevents_repeat_email(self):
        url = reverse('resend_verification')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_link_changes_password(self):
        self.client.logout()
        self.client.post(reverse('password_reset'), {'email': self.user.email})
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'http://[^\s]+', mail.outbox[0].body).group(0)
        path = '/' + url.split('/', 3)[3]
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(response.url, {'new_password1': 'NewSecurePass432!', 'new_password2': 'NewSecurePass432!'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass432!'))

    def test_unknown_reset_email_has_same_response(self):
        self.client.logout()
        response = self.client.post(reverse('password_reset'), {'email': 'absent@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_profile_keeps_teaching_and_learning_skills_separate(self):
        teaching = Skill.objects.create(name='Python')
        learning = Skill.objects.create(name='React')
        response = self.client.post(reverse('profile_edit'), {'first_name': 'Learner', 'last_name': '', 'email': self.user.email,
            'bio': 'Bio', 'experience_level': 'Beginner', 'availability': 'Flexible', 'is_learner': 'on',
            'skills': [teaching.pk], 'learning_skills': [learning.pk], 'timezone': 'Asia/Kolkata', 'mentor_capacity': 3,
            'portfolio_url': 'https://example.com/portfolio'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.user.profile.skills.all()), [teaching])
        self.assertEqual(list(self.user.profile.learning_skills.all()), [learning])
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.timezone, 'Asia/Kolkata')

    def test_email_change_invalidates_verification(self):
        self.user.profile.email_verified = True
        self.user.profile.save()
        self.client.post(reverse('profile_edit'), {'email': 'new@example.com', 'first_name': '', 'last_name': '', 'experience_level': 'Beginner', 'availability': 'Flexible', 'is_learner': 'on'})
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_rejects_invalid_timezone_and_capacity(self):
        response = self.client.post(reverse('profile_edit'), {'email': self.user.email, 'experience_level': 'Beginner',
            'availability': 'Flexible', 'is_learner': 'on', 'timezone': 'Invalid/Zone', 'mentor_capacity': 0})
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.mentor_capacity, 5)

    def test_zero_capacity_is_rejected(self):
        response = self.client.post(reverse('profile_edit'), {'email': self.user.email, 'experience_level': 'Beginner',
            'availability': 'Flexible', 'is_learner': 'on', 'timezone': 'UTC', 'mentor_capacity': 0})
        self.assertEqual(response.status_code, 200)
        self.assertIn('mentor_capacity', response.context['profile_form'].errors)

    def test_invalid_skill_input_returns_form_error(self):
        response = self.client.post(reverse('profile_edit'), {'email': self.user.email, 'experience_level': 'Beginner',
            'availability': 'Flexible', 'is_learner': 'on', 'skills': ['not-an-id']})
        self.assertEqual(response.status_code, 200)
        self.assertIn('skills', response.context['profile_form'].errors)

    def test_verification_request_cannot_self_verify(self):
        self.client.force_login(self.mentor)
        self.client.post(reverse('mentor_verification_request'), {'evidence': 'Portfolio and five years of mentoring experience.'})
        self.mentor.profile.refresh_from_db()
        self.assertTrue(self.mentor.profile.verification_requested)
        self.assertFalse(self.mentor.profile.mentor_verified)

    def test_report_is_private_and_stored_for_admin_review(self):
        response = self.client.post(reverse('report_user', args=[self.mentor.pk]), {'reason': 'PROFILE', 'details': 'Please review these claims.'})
        self.assertEqual(response.status_code, 302)
        report = UserReport.objects.get()
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.reported_user, self.mentor)
        self.assertEqual(report.status, 'OPEN')
        self.assertEqual(self.client.get(reverse('report_user', args=[self.user.pk])).status_code, 403)

    def test_saved_mentor_operations_are_idempotent(self):
        url = reverse('save_mentor', args=[self.mentor.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {'action': 'save'})
        self.client.post(url, {'action': 'save'})
        self.assertEqual(SavedMentor.objects.count(), 1)
        self.assertContains(self.client.get(reverse('mentor_list')+'?saved=1'), 'mentor')
        self.client.post(url, {'action': 'remove'})
        self.assertFalse(SavedMentor.objects.exists())

    def test_weekly_slots_reject_overlap_and_backwards_times(self):
        self.client.force_login(self.mentor)
        url = reverse('availability_settings')
        self.client.post(url, {'weekday': 0, 'start_time': '09:00', 'end_time': '11:00'})
        self.assertContains(self.client.post(url, {'weekday': 0, 'start_time': '10:00', 'end_time': '12:00'}), 'overlaps')
        self.assertContains(self.client.post(url, {'weekday': 1, 'start_time': '12:00', 'end_time': '10:00'}), 'after start')
        self.assertEqual(AvailabilitySlot.objects.count(), 1)

    def test_cannot_remove_another_mentors_slot(self):
        from datetime import time
        slot = AvailabilitySlot.objects.create(user=self.mentor, weekday=0, start_time=time(9), end_time=time(11))
        self.assertEqual(self.client.post(reverse('availability_delete', args=[slot.pk])).status_code, 404)

    def test_matching_uses_learning_goals_instead_of_teaching_skills(self):
        skill = Skill.objects.create(name='Python')
        self.user.profile.skills.add(skill)
        self.mentor.profile.skills.add(skill)
        before = calculate_match_score(self.user.profile, self.mentor.profile)
        self.assertEqual(before['shared_skill_count'], 0)
        self.user.profile.learning_skills.add(skill)
        after = calculate_match_score(self.user.profile, self.mentor.profile)
        self.assertEqual(after['shared_skill_count'], 1)

    def test_dashboard_shows_live_sessions_progress_tasks_and_wallet(self):
        mentorship = Mentorship.objects.create(mentor=self.mentor, learner=self.user, goals='Learn Python', status='ACTIVE')
        Progress.objects.create(mentorship=mentorship, completion_pct=70)
        Session.objects.create(mentorship=mentorship, date=timezone.now()+timezone.timedelta(days=2))
        Milestone.objects.create(mentorship=mentorship, title='Finish project')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Upcoming meetings')
        self.assertContains(response, 'Finish project')
        self.assertContains(response, '70.0%')
        self.assertNotContains(response, 'Available in Phase 3')

    @override_settings(DEBUG=True)
    def test_default_seeder_preserves_existing_demo_activity(self):
        demo = User.objects.create_user('sarah_backend', password='CustomPassword')
        mentorship = Mentorship.objects.create(mentor=demo, learner=self.user, goals='Keep this')
        output = StringIO()
        call_command('seed_demo_data', stdout=output)
        self.assertTrue(User.objects.filter(pk=demo.pk).exists())
        self.assertTrue(Mentorship.objects.filter(pk=mentorship.pk).exists())
        self.assertIn('preserved', output.getvalue())

    @override_settings(DEBUG=True)
    def test_fresh_demo_seed_provisions_verifiable_certificate(self):
        call_command('seed_demo_data', stdout=StringIO())
        completed = Mentorship.objects.get(status='COMPLETED')
        self.assertTrue(completed.certificate_id)
        self.assertEqual(completed.certificate_data['learner'], 'Priya Sharma')
        self.assertEqual(self.client.get(reverse('certificate_verify', args=[completed.certificate_id])).status_code, 200)

    def test_external_login_redirect_is_rejected(self):
        self.client.logout()
        response = self.client.post(reverse('login')+'?next=https://example.com/', {'username': self.user.username, 'password': 'Pass123!'})
        self.assertRedirects(response, reverse('dashboard'))
