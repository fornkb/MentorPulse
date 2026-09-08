from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost


class MentorshipModelTests(TestCase):
    def setUp(self):
        self.mentor = User.objects.create_user(username='mentor_user', password='password')
        self.learner = User.objects.create_user(username='learner_user', password='password')
        self.stranger = User.objects.create_user(username='stranger_user', password='password')

        self.mentorship = Mentorship.objects.create(
            mentor=self.mentor,
            learner=self.learner,
            goals="Learn advanced React component design and testing.",
            is_priority=True,
            status='ACTIVE'
        )
        self.progress = Progress.objects.create(mentorship=self.mentorship)

    def test_mentorship_access_permissions(self):
        """Participants and staff can access, strangers cannot."""
        self.assertTrue(self.mentorship.can_access(self.mentor))
        self.assertTrue(self.mentorship.can_access(self.learner))
        self.assertFalse(self.mentorship.can_access(self.stranger))

    def test_progress_recalculation_empty(self):
        """When no milestones or sessions exist, progress is 0.0%."""
        pct = self.progress.recalculate()
        self.assertEqual(pct, 0.0)

    def test_progress_recalculation_weighted(self):
        """
        Progress is weighted:
        - Milestones: 70%
        - Sessions: 30%
        """
        # Create 2 milestones (1 completed -> 50% of 70% = 35%)
        Milestone.objects.create(mentorship=self.mentorship, title="Setup repository", is_completed=True)
        Milestone.objects.create(mentorship=self.mentorship, title="Write tests", is_completed=False)

        # Create 2 sessions (1 completed -> 50% of 30% = 15%)
        Session.objects.create(mentorship=self.mentorship, date=timezone.now(), is_completed=True)
        Session.objects.create(mentorship=self.mentorship, date=timezone.now(), is_completed=False)

        pct = self.progress.recalculate()
        self.assertEqual(pct, 50.0)

    def test_progress_recalculation_completed_status(self):
        """When status is COMPLETED, progress is always 100%."""
        self.mentorship.status = 'COMPLETED'
        self.mentorship.save()
        pct = self.progress.recalculate()
        self.assertEqual(pct, 100.0)
