from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import Skill, Profile, RoleAssignment
from .models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost


class MentorshipFlowTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Skill
        self.skill = Skill.objects.create(name='React', category='Programming')

        # Mentor
        self.mentor = User.objects.create_user(username='mentor_alice', password='password123')
        RoleAssignment.objects.create(user=self.mentor, role='Mentor')
        self.mentor.profile.skills.add(self.skill)

        # Learner
        self.learner = User.objects.create_user(username='learner_bob', password='password123')
        RoleAssignment.objects.create(user=self.learner, role='Learner')
        self.learner.profile.skills.add(self.skill)

        # Third-party user
        self.other_user = User.objects.create_user(username='charlie', password='password123')

    def test_request_mentorship_success(self):
        """Learner can submit a mentorship request with goals and priority."""
        self.client.login(username='learner_bob', password='password123')
        response = self.client.post(
            reverse('mentorship_request', kwargs={'mentor_id': self.mentor.id}),
            {
                'goals': 'Master state management and component architecture.',
                'is_priority': True,
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Mentorship.objects.filter(learner=self.learner, mentor=self.mentor).exists())
        mentorship = Mentorship.objects.get(learner=self.learner, mentor=self.mentor)
        self.assertEqual(mentorship.status, 'PENDING')
        self.assertTrue(mentorship.is_priority)

    def test_request_self_prevented(self):
        """User cannot request mentorship from themselves."""
        self.client.login(username='mentor_alice', password='password123')
        response = self.client.post(
            reverse('mentorship_request', kwargs={'mentor_id': self.mentor.id}),
            {'goals': 'Self coaching'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Mentorship.objects.filter(learner=self.mentor, mentor=self.mentor).exists())

    def test_mentor_accept_workflow(self):
        """Mentor accepts pending request, transitioning to ACTIVE and creating progress."""
        mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            goals='Learn React',
            status='PENDING'
        )
        self.client.login(username='mentor_alice', password='password123')
        response = self.client.get(reverse('mentorship_accept', kwargs={'mentorship_id': mentorship.id}))
        self.assertEqual(response.status_code, 302)

        mentorship.refresh_from_db()
        self.assertEqual(mentorship.status, 'ACTIVE')
        self.assertTrue(hasattr(mentorship, 'progress'))
        self.assertTrue(mentorship.discussion_posts.exists())

    def test_workspace_access_control(self):
        """Unauthorized users cannot access the workspace."""
        mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            goals='Learn React',
            status='ACTIVE'
        )
        Progress.objects.create(mentorship=mentorship)

        # Stranger access -> 403 Forbidden
        self.client.login(username='charlie', password='password123')
        response = self.client.get(reverse('mentorship_workspace', kwargs={'mentorship_id': mentorship.id}))
        self.assertEqual(response.status_code, 403)

        # Learner access -> 200 OK
        self.client.login(username='learner_bob', password='password123')
        response = self.client.get(reverse('mentorship_workspace', kwargs={'mentorship_id': mentorship.id}))
        self.assertEqual(response.status_code, 200)

    def test_milestone_and_session_progress_tracking(self):
        """Adding and toggling milestones and sessions updates progress percentage."""
        mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            goals='Learn React',
            status='ACTIVE'
        )
        Progress.objects.create(mentorship=mentorship)

        self.client.login(username='mentor_alice', password='password123')

        # Add milestone
        self.client.post(
            reverse('milestone_add', kwargs={'mentorship_id': mentorship.id}),
            {'title': 'Build first component'}
        )
        self.assertEqual(mentorship.milestones.count(), 1)
        milestone = mentorship.milestones.first()

        # Toggle milestone complete
        self.client.get(reverse('milestone_toggle', kwargs={'milestone_id': milestone.id}))
        milestone.refresh_from_db()
        self.assertTrue(milestone.is_completed)
        mentorship.progress.refresh_from_db()
        self.assertEqual(mentorship.progress.completion_pct, 100.0)

    def test_resource_upload_validation(self):
        """Resource form rejects invalid file types."""
        mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            goals='Learn React',
            status='ACTIVE'
        )
        self.client.login(username='mentor_alice', password='password123')

        # Valid text file
        valid_file = SimpleUploadedFile("notes.txt", b"Hello world notes", content_type="text/plain")
        response = self.client.post(
            reverse('resource_add', kwargs={'mentorship_id': mentorship.id}),
            {
                'title': 'Meeting Notes',
                'type': 'FILE',
                'file': valid_file,
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resource.objects.filter(mentorship=mentorship, title='Meeting Notes').exists())

    def test_completion_and_certificate_flow(self):
        """Completing a mentorship unlocks the print-friendly certificate."""
        mentorship = Mentorship.objects.create(
            learner=self.learner,
            mentor=self.mentor,
            goals='Learn React',
            status='ACTIVE'
        )
        Progress.objects.create(mentorship=mentorship)
        self.client.login(username='mentor_alice', password='password123')

        # Complete mentorship
        response = self.client.post(reverse('mentorship_complete', kwargs={'mentorship_id': mentorship.id}))
        self.assertEqual(response.status_code, 302)
        mentorship.refresh_from_db()
        mentorship.progress.refresh_from_db()
        self.assertEqual(mentorship.status, 'COMPLETED')
        self.assertEqual(mentorship.progress.completion_pct, 100.0)


        # Access certificate
        cert_response = self.client.get(reverse('mentorship_certificate', kwargs={'mentorship_id': mentorship.id}))
        self.assertEqual(cert_response.status_code, 200)
        self.assertContains(cert_response, 'Certificate of Completion')
        self.assertContains(cert_response, 'learner_bob')
