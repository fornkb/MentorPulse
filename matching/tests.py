from django.test import TestCase
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
        # Verify scores are generated without error
        self.assertIn('score', ranked[0])
        self.assertIn('score', ranked[1])
