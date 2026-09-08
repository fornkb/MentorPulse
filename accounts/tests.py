from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Skill, Profile, RoleAssignment


class AccountsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.skill_python = Skill.objects.create(name='Python', category='Programming')
        self.skill_design = Skill.objects.create(name='UI/UX Design', category='Design')

    def test_profile_auto_created_on_user_creation(self):
        """Verify post_save signal automatically creates a linked Profile."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.experience_level, 'Beginner')

    def test_initial_role_assignment(self):
        """Verify post_save signal creates an initial Learner role."""
        self.assertTrue(self.user.profile.is_learner)
        self.assertFalse(self.user.profile.is_mentor)
        self.assertIn('Learner', self.user.profile.active_roles)

    def test_role_assignment_toggle(self):
        """Verify activating Mentor role and helper properties."""
        RoleAssignment.objects.create(user=self.user, role='Mentor')
        self.assertTrue(self.user.profile.is_mentor)
        self.assertTrue(self.user.profile.is_learner)
        self.assertEqual(set(self.user.profile.active_roles), {'Mentor', 'Learner'})

    def test_skill_association(self):
        """Verify assigning skills to profile."""
        self.user.profile.skills.add(self.skill_python, self.skill_design)
        self.assertEqual(self.user.profile.skills.count(), 2)
        self.assertIn(self.skill_python, self.user.profile.skills.all())


class AccountsViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='TestPassword123!'
        )
        self.skill = Skill.objects.create(name='Django', category='Programming')

    def test_register_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_post_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'register_as_learner': True,
            'register_as_mentor': True,
        })
        self.assertEqual(response.status_code, 302)  # Redirects to profile_edit
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.profile.is_mentor)
        self.assertTrue(new_user.profile.is_learner)

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'mismatch',
            'first_name': 'Mis',
            'last_name': 'Match',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'DifferentPassword123!',
            'register_as_learner': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'confirm_password', 'Passwords do not match.')


    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'existinguser',
            'password': 'TestPassword123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'existinguser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")

    def test_dashboard_login_required(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_authenticated(self):
        self.client.login(username='existinguser', password='TestPassword123!')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')

    def test_profile_edit(self):
        self.client.login(username='existinguser', password='TestPassword123!')
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'existing@example.com',
            'bio': 'Updated bio information',
            'experience_level': 'Advanced',
            'availability': 'Weekdays',
            'goals': 'Master Django testing',
            'skills': [self.skill.id],
            'is_mentor': True,
            'is_learner': True,
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.profile.bio, 'Updated bio information')
        self.assertEqual(self.user.profile.experience_level, 'Advanced')
        self.assertTrue(self.user.profile.is_mentor)
        self.assertIn(self.skill, self.user.profile.skills.all())
