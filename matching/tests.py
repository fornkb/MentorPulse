from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Skill, Profile, RoleAssignment
from matching.services import calculate_match_score, rank_mentors_for_learner


class MatchingEngineTests(TestCase):
    def setUp(self):
        # Create Skills
        self.skill_py = Skill.objects.create(name='Python', category='Programming')
        self.skill_dj = Skill.objects.create(name='Django', category='Programming')
        self.skill_figma = Skill.objects.create(name='Figma', category='Design')

        # Learner
        self.learner_user = User.objects.create_user(username='test_learner', password='password')
        self.learner_profile = self.learner_user.profile
        self.learner_profile.experience_level = 'Beginner'
        self.learner_profile.availability = 'Weekdays'
        self.learner_profile.skills.add(self.skill_py, self.skill_dj)
        self.learner_profile.save()

        # Mentor 1: High Match (Teaches Python & Django, Advanced, Weekdays)
        self.mentor_high = User.objects.create_user(username='mentor_high', password='password')
        RoleAssignment.objects.create(user=self.mentor_high, role='Mentor')
        self.profile_high = self.mentor_high.profile
        self.profile_high.experience_level = 'Advanced'
        self.profile_high.availability = 'Weekdays'
        self.profile_high.skills.add(self.skill_py, self.skill_dj)
        self.profile_high.save()

        # Mentor 2: Low Match (Teaches only Figma, Beginner, Weekends)
        self.mentor_low = User.objects.create_user(username='mentor_low', password='password')
        RoleAssignment.objects.create(user=self.mentor_low, role='Mentor')
        self.profile_low = self.mentor_low.profile
        self.profile_low.experience_level = 'Beginner'
        self.profile_low.availability = 'Weekends'
        self.profile_low.skills.add(self.skill_figma)
        self.profile_low.save()

    def test_high_match_score(self):
        result = calculate_match_score(self.learner_profile, self.profile_high)
        self.assertGreaterEqual(result['total_score'], 85)
        self.assertEqual(result['skill_percentage'], 100)
        self.assertEqual(result['availability_percentage'], 100)
        self.assertEqual(len(result['shared_skills']), 2)

    def test_low_match_score(self):
        result = calculate_match_score(self.learner_profile, self.profile_low)
        self.assertLessEqual(result['total_score'], 35)
        self.assertEqual(result['skill_percentage'], 0)
        self.assertEqual(len(result['shared_skills']), 0)

    def test_rank_mentors_ordering(self):
        mentors = [self.mentor_low, self.mentor_high]
        ranked = rank_mentors_for_learner(self.learner_user, mentors)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]['mentor'], self.mentor_high)
        self.assertEqual(ranked[1]['mentor'], self.mentor_low)
        self.assertGreater(ranked[0]['score'], ranked[1]['score'])

    def test_anonymous_learner_ranking(self):
        mentors = [self.mentor_high, self.mentor_low]
        ranked = rank_mentors_for_learner(None, mentors)
        self.assertEqual(len(ranked), 2)
        self.assertIn('score', ranked[0])
        self.assertIn('score', ranked[1])


class MatchingViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Skills
        self.skill_python = Skill.objects.create(name='Python', category='Programming')
        self.skill_design = Skill.objects.create(name='UI/UX Design', category='Design')

        # Active Mentor
        self.mentor = User.objects.create_user(
            username='active_mentor',
            first_name='Marcus',
            last_name='Aurelius',
            password='Password123!'
        )
        RoleAssignment.objects.create(user=self.mentor, role='Mentor')
        self.mentor.profile.skills.add(self.skill_python)
        self.mentor.profile.experience_level = 'Expert'
        self.mentor.profile.availability = 'Weekdays'
        self.mentor.profile.bio = 'Python and backend architect with philosophy.'
        self.mentor.profile.save()

        # Non-mentor user
        self.learner = User.objects.create_user(
            username='solo_learner',
            password='Password123!'
        )
        self.learner.profile.skills.add(self.skill_python)
        self.learner.profile.save()

    def test_directory_view_guest(self):
        """Unauthenticated guest can browse mentor directory."""
        response = self.client.get(reverse('mentor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matching/mentor_list.html')
        self.assertContains(response, 'Marcus Aurelius')
        # solo_learner should NOT appear since they do not have an active Mentor role
        self.assertNotContains(response, '@solo_learner')

    def test_directory_view_search_filter(self):
        """Search by query parameter."""
        # Query matches Marcus
        response = self.client.get(reverse('mentor_list') + '?q=Marcus')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Aurelius')

        # Query does not match
        response_empty = self.client.get(reverse('mentor_list') + '?q=NonExistentMentor')
        self.assertEqual(response_empty.status_code, 200)
        self.assertContains(response_empty, 'No mentors found')

    def test_directory_view_skill_filter(self):
        """Filter by skill name."""
        response = self.client.get(reverse('mentor_list') + '?skill=Python')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Aurelius')

        response_empty = self.client.get(reverse('mentor_list') + '?skill=UI/UX Design')
        self.assertEqual(response_empty.status_code, 200)
        self.assertContains(response_empty, 'No mentors found')

    def test_directory_view_experience_and_availability_filters(self):
        """Filter by experience level and availability."""
        response = self.client.get(reverse('mentor_list') + '?experience=Expert&availability=Weekdays')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marcus Aurelius')

        response_none = self.client.get(reverse('mentor_list') + '?experience=Beginner')
        self.assertEqual(response_none.status_code, 200)
        self.assertContains(response_none, 'No mentors found')

    def test_mentor_detail_view(self):
        """Public mentor detail page displays bio and skills."""
        response = self.client.get(reverse('mentor_detail', kwargs={'user_id': self.mentor.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matching/mentor_detail.html')
        self.assertContains(response, 'Marcus Aurelius')
        self.assertContains(response, 'Python')

    def test_mentor_detail_with_learner_analysis(self):
        """When a learner views a mentor, match breakdown is rendered."""
        self.client.login(username='solo_learner', password='Password123!')
        response = self.client.get(reverse('mentor_detail', kwargs={'user_id': self.mentor.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Match Compatibility Analysis')
        self.assertContains(response, 'Skill Overlap')
