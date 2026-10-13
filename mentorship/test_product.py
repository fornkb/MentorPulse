from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, time
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import RoleAssignment, AvailabilitySlot
from gamification.models import CreditTransaction
from gamification.services import CreditService
from .models import Mentorship, Progress, Session, Milestone, Resource
from .services import create_request, transition_request, complete_mentorship, save_session
from .forms import SessionForm, ResourceForm


class ProductWorkflowTests(TestCase):
    def setUp(self):
        self.mentor = User.objects.create_user('mentor', password='Pass123!')
        RoleAssignment.objects.create(user=self.mentor, role='Mentor')
        self.learner = User.objects.create_user('learner', password='Pass123!')
        self.stranger = User.objects.create_user('stranger', password='Pass123!')
        self.mentorship = Mentorship.objects.create(mentor=self.mentor, learner=self.learner, goals='Learn', status='ACTIVE')
        Progress.objects.create(mentorship=self.mentorship)
        self.client.force_login(self.mentor)

    def session_data(self, date=None, duration=60):
        return {'date': (date or timezone.now() + timedelta(days=2)).isoformat(),
                'duration_minutes': duration, 'notes': 'Agenda', 'meeting_link': ''}

    def ready_to_complete(self):
        Milestone.objects.create(mentorship=self.mentorship, title='Deliver project', is_completed=True)
        return Session.objects.create(mentorship=self.mentorship, date=timezone.now() - timedelta(days=1), is_completed=True)

    def test_request_failure_rolls_back_wallet_ledger_and_request(self):
        self.mentorship.status = 'COMPLETED'
        self.mentorship.save()
        with patch('mentorship.services.send_notification', side_effect=RuntimeError('notification failure')):
            with self.assertRaises(RuntimeError):
                create_request(self.learner, self.mentor, 'New goals', True)
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 50)
        self.assertFalse(CreditTransaction.objects.filter(user=self.learner, amount__lt=0).exists())
        self.assertFalse(Mentorship.objects.filter(status='PENDING').exists())

    def test_insufficient_wallet_creates_no_request(self):
        self.mentorship.status = 'COMPLETED'
        self.mentorship.save()
        self.learner.credit.balance = 4
        self.learner.credit.save()
        with self.assertRaises(ValidationError):
            create_request(self.learner, self.mentor, 'New goals', False)
        self.assertFalse(Mentorship.objects.filter(status='PENDING').exists())

    def test_duplicate_request_is_not_charged_again(self):
        self.mentorship.status = 'COMPLETED'
        self.mentorship.save()
        create_request(self.learner, self.mentor, 'New goals', False)
        with self.assertRaises(ValidationError):
            create_request(self.learner, self.mentor, 'New goals', False)
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 40)

    def test_credit_and_ledger_rollback_on_failed_ledger_insert(self):
        with patch('gamification.services.CreditTransaction.objects.create', side_effect=RuntimeError('ledger failure')):
            with self.assertRaises(RuntimeError):
                CreditService.deduct_for_request(self.learner, True)
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 50)

    def test_repeated_refund_is_credited_once(self):
        self.mentorship.status = 'COMPLETED'
        self.mentorship.save()
        pending = create_request(self.learner, self.mentor, 'New goals', True)
        transition_request(pending.pk, self.mentor, 'REJECTED')
        self.assertFalse(CreditService.refund_for_request(pending))
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 50)
        self.assertEqual(CreditTransaction.objects.filter(event_key=f'refund:{pending.pk}').count(), 1)

    def test_database_prevents_duplicate_open_pair(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Mentorship.objects.create(mentor=self.mentor, learner=self.learner, goals='Duplicate')

    def test_database_prevents_negative_wallet(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            type(self.learner.credit).objects.filter(user=self.learner).update(balance=-1)

    def test_capacity_blocks_request_and_acceptance(self):
        self.mentor.profile.mentor_capacity = 1
        self.mentor.profile.save()
        with self.assertRaises(ValidationError):
            create_request(self.stranger, self.mentor, 'More goals', False)
        pending = Mentorship.objects.create(mentor=self.mentor, learner=self.stranger, goals='Pending')
        with self.assertRaises(ValidationError):
            transition_request(pending.pk, self.mentor, 'ACTIVE')
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'PENDING')

    def test_get_cannot_change_lifecycle_or_milestones(self):
        milestone = Milestone.objects.create(mentorship=self.mentorship, title='Todo')
        for name, pk in [('milestone_toggle', milestone.pk), ('mentorship_complete', self.mentorship.pk), ('mentorship_accept', self.mentorship.pk)]:
            self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 405)

    def test_learner_cannot_issue_certificate(self):
        self.ready_to_complete()
        self.client.force_login(self.learner)
        self.assertEqual(self.client.post(reverse('mentorship_complete', args=[self.mentorship.pk])).status_code, 403)
        self.assertFalse(Mentorship.objects.get(pk=self.mentorship.pk).certificate_id)

    def test_incomplete_roadmap_does_not_unlock_certificate(self):
        Milestone.objects.create(mentorship=self.mentorship, title='Todo')
        with self.assertRaises(ValidationError):
            complete_mentorship(self.mentorship.pk, self.mentor)
        self.mentorship.refresh_from_db()
        self.assertEqual(self.mentorship.status, 'ACTIVE')
        self.assertIsNone(self.mentorship.certificate_id)

    def test_finished_milestones_without_session_cannot_complete(self):
        Milestone.objects.create(mentorship=self.mentorship, title='Done', is_completed=True)
        with self.assertRaises(ValidationError):
            complete_mentorship(self.mentorship.pk, self.mentor)

    def test_cancelled_session_does_not_block_completion(self):
        self.ready_to_complete()
        Session.objects.create(mentorship=self.mentorship, date=timezone.now() + timedelta(days=2), is_cancelled=True)
        completed = complete_mentorship(self.mentorship.pk, self.mentor)
        self.assertEqual(completed.status, 'COMPLETED')
        self.assertTrue(completed.certificate_id)

    def test_certificate_names_remain_stable_after_profile_changes(self):
        self.ready_to_complete()
        completed = complete_mentorship(self.mentorship.pk, self.mentor)
        self.learner.first_name = 'Changed name'
        self.learner.save()
        response = self.client.get(reverse('certificate_verify', args=[completed.certificate_id]))
        self.assertContains(response, '<dd>learner</dd>', html=True)
        self.assertNotContains(response, 'Changed name')

    def test_certificate_verify_is_public_but_pdf_is_private(self):
        self.ready_to_complete()
        completed = complete_mentorship(self.mentorship.pk, self.mentor)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('certificate_verify', args=[completed.certificate_id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('certificate_verify', args=[uuid4()])).status_code, 404)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('certificate_pdf', args=[completed.pk])).status_code, 403)
        self.client.force_login(self.learner)
        response = self.client.get(reverse('certificate_pdf', args=[completed.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))

    def test_completed_workspace_rejects_mutations(self):
        self.ready_to_complete()
        completed = complete_mentorship(self.mentorship.pk, self.mentor)
        milestone = completed.milestones.first()
        for name, args, data in [('milestone_toggle', [milestone.pk], {}), ('milestone_add', [completed.pk], {'title': 'New'}),
                                 ('resource_add', [completed.pk], {'title': 'Note', 'type': 'NOTE', 'content': 'New'}),
                                 ('discussion_post', [completed.pk], {'text': 'Late change'}),
                                 ('session_add', [completed.pk], self.session_data())]:
            self.assertEqual(self.client.post(reverse(name, args=args), data).status_code, 403)
        self.assertNotContains(self.client.get(reverse('mentorship_workspace', args=[completed.pk])), 'Confirm completed')

    def test_repeat_session_confirmation_rewards_once(self):
        session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()-timedelta(days=1))
        url = reverse('session_toggle', args=[session.pk])
        self.client.post(url)
        self.client.post(url)
        self.mentor.credit.refresh_from_db()
        self.assertEqual(self.mentor.credit.balance, 60)
        self.assertEqual(CreditTransaction.objects.filter(event_key=f'session:{session.pk}').count(), 1)

    def test_future_session_cannot_be_confirmed_or_rewarded(self):
        session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()+timedelta(days=1))
        self.client.post(reverse('session_toggle', args=[session.pk]))
        self.assertFalse(Session.objects.get(pk=session.pk).is_completed)
        self.assertFalse(CreditTransaction.objects.filter(event_key=f'session:{session.pk}').exists())

    def test_learner_cannot_confirm_session_reward(self):
        session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()-timedelta(days=1))
        self.client.force_login(self.learner)
        self.assertEqual(self.client.post(reverse('session_toggle', args=[session.pk])).status_code, 403)

    def test_schedule_uses_profile_timezone(self):
        self.mentor.profile.timezone = 'Asia/Kolkata'
        self.mentor.profile.save()
        date = (timezone.now()+timedelta(days=2)).date()
        response = self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data().copy() | {'date': f'{date}T10:00'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mentorship.sessions.get().date.hour, 4)
        self.assertEqual(self.mentorship.sessions.get().date.minute, 30)

    def test_overlapping_session_is_rejected_and_form_preserved(self):
        date = timezone.now()+timedelta(days=2)
        Session.objects.create(mentorship=self.mentorship, date=date, duration_minutes=60)
        response = self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data(date+timedelta(minutes=30)))
        self.assertContains(response, 'overlaps another session')
        self.assertEqual(self.mentorship.sessions.count(), 1)
        self.assertContains(response, 'Agenda')

    def test_boundary_session_can_be_scheduled(self):
        date = timezone.now()+timedelta(days=2)
        Session.objects.create(mentorship=self.mentorship, date=date, duration_minutes=60)
        self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data(date+timedelta(minutes=60)))
        self.assertEqual(self.mentorship.sessions.count(), 2)

    def test_conflicts_across_different_mentorships_are_rejected(self):
        date = timezone.now()+timedelta(days=2)
        other = Mentorship.objects.create(mentor=self.stranger, learner=self.learner, status='ACTIVE', goals='Other')
        Session.objects.create(mentorship=other, date=date)
        form = SessionForm(self.session_data(date))
        self.assertTrue(form.is_valid())
        with self.assertRaises(ValidationError):
            save_session(form, self.mentorship, self.mentor)

    def test_published_availability_is_enforced(self):
        date = (timezone.now()+timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
        AvailabilitySlot.objects.create(user=self.mentor, weekday=date.weekday(), start_time=time(9), end_time=time(11))
        self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data(date))
        response = self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data(date+timedelta(hours=2)))
        self.assertContains(response, 'published availability')
        self.assertEqual(self.mentorship.sessions.count(), 1)

    def test_past_and_invalid_duration_sessions_are_rejected(self):
        url = reverse('session_add', args=[self.mentorship.pk])
        self.assertContains(self.client.post(url, self.session_data(timezone.now()-timedelta(days=1))), 'future date')
        self.assertEqual(self.client.post(url, self.session_data(duration=241)).status_code, 200)
        self.assertFalse(self.mentorship.sessions.exists())

    def test_reschedule_resets_reminder_and_preserves_session_id(self):
        session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()+timedelta(days=2), reminder_sent_at=timezone.now())
        self.client.post(reverse('session_edit', args=[session.pk]), self.session_data(timezone.now()+timedelta(days=3)))
        session.refresh_from_db()
        self.assertIsNone(session.reminder_sent_at)
        self.assertEqual(self.mentorship.sessions.count(), 1)

    def test_cancellation_frees_slot_and_is_idempotent(self):
        date = timezone.now()+timedelta(days=2)
        session = Session.objects.create(mentorship=self.mentorship, date=date)
        self.client.post(reverse('session_cancel', args=[session.pk]))
        self.client.post(reverse('session_cancel', args=[session.pk]))
        self.client.post(reverse('session_add', args=[self.mentorship.pk]), self.session_data(date))
        self.assertEqual(self.mentorship.sessions.filter(is_cancelled=False).count(), 1)

    def test_calendar_export_is_private_utc_and_escaped(self):
        session = Session.objects.create(mentorship=self.mentorship, date=timezone.now()+timedelta(days=2), notes='Hello, world; next\n' + 'é'*100)
        response = self.client.get(reverse('session_calendar', args=[session.pk]))
        self.assertContains(response, 'BEGIN:VCALENDAR')
        self.assertContains(response, 'Hello\\, world\\; next\\n')
        self.assertTrue(all(len(line) <= 75 for line in response.content.split(b'\r\n')))
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('session_calendar', args=[session.pk])).status_code, 403)

    def test_edit_milestone_updates_deadline(self):
        milestone = Milestone.objects.create(mentorship=self.mentorship, title='Old')
        response = self.client.post(reverse('milestone_edit', args=[milestone.pk]), {'title': 'New', 'due_date': '2030-01-01'})
        self.assertEqual(response.status_code, 302)
        milestone.refresh_from_db()
        self.assertEqual(milestone.title, 'New')
        self.assertEqual(str(milestone.due_date), '2030-01-01')

    def test_unsafe_resource_link_rejected(self):
        for value in ['javascript:alert(1)', 'data:text/html,x', 'not-a-link']:
            self.assertFalse(ResourceForm({'title': 'Unsafe', 'type': 'LINK', 'content': value}).is_valid())

    def test_resource_download_checks_membership(self):
        resource = Resource.objects.create(mentorship=self.mentorship, uploaded_by=self.mentor, title='Notes', type='FILE',
            file=SimpleUploadedFile('notes.txt', b'Private notes'))
        response = self.client.get(reverse('resource_download', args=[resource.pk]))
        self.assertEqual(b''.join(response.streaming_content), b'Private notes')
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('resource_download', args=[resource.pk])).status_code, 403)
        self.assertEqual(self.client.get(resource.file.url).status_code, 404)


class ConcurrentCreditTests(TransactionTestCase):
    def setUp(self):
        self.mentor = User.objects.create_user('concurrent_mentor')
        RoleAssignment.objects.create(user=self.mentor, role='Mentor')
        self.learner = User.objects.create_user('concurrent_learner')

    def parallel(self, operation):
        barrier = Barrier(2)
        def run(_):
            close_old_connections()
            barrier.wait(timeout=5)
            try:
                return operation()
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(run, range(2)))

    def test_two_spenders_cannot_overdraw_or_lose_ledger_entries(self):
        self.learner.credit.balance = 10
        self.learner.credit.save()
        results = self.parallel(lambda: CreditService.deduct_for_request(self.learner)[0])
        self.assertEqual(sorted(results), [False, True])
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 0)
        self.assertEqual(CreditTransaction.objects.filter(user=self.learner, reason='SESSION_REQUEST').count(), 1)

    def test_concurrent_retries_create_one_request_and_one_charge(self):
        def request():
            try:
                return create_request(self.learner, self.mentor, 'Goals', False).pk
            except ValidationError:
                return None
        results = self.parallel(request)
        self.assertEqual(sum(pk is not None for pk in results), 1)
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 40)
        self.assertEqual(Mentorship.objects.count(), 1)

    def test_concurrent_refunds_credit_once(self):
        pending = create_request(self.learner, self.mentor, 'Goals', False)
        results = self.parallel(lambda: CreditService.refund_for_request(pending))
        self.assertEqual(sorted(results), [False, True])
        self.learner.credit.refresh_from_db()
        self.assertEqual(self.learner.credit.balance, 50)
