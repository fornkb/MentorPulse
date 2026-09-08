from django.db import models
from django.contrib.auth.models import User


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('Programming', 'Programming'),
        ('Design', 'Design'),
        ('Data', 'Data Science & AI'),
        ('Business', 'Business & Product'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Programming')

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Profile(models.Model):
    EXPERIENCE_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]

    AVAILABILITY_CHOICES = [
        ('Weekdays', 'Weekdays'),
        ('Weekends', 'Weekends'),
        ('Flexible', 'Flexible / Evenings'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    skills = models.ManyToManyField(Skill, blank=True, related_name='profiles')
    goals = models.TextField(blank=True, help_text="Learning or mentoring objectives")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='Beginner')
    availability = models.CharField(max_length=50, choices=AVAILABILITY_CHOICES, default='Flexible')
    skill_score = models.FloatField(default=0.0)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def is_mentor(self):
        """Check if user has an active Mentor role assignment."""
        return self.user.role_assignments.filter(role='Mentor', end_time__isnull=True).exists()

    @property
    def is_learner(self):
        """Check if user has an active Learner role assignment."""
        return self.user.role_assignments.filter(role='Learner', end_time__isnull=True).exists()

    @property
    def active_roles(self):
        """Return list of active role strings."""
        return list(self.user.role_assignments.filter(end_time__isnull=True).values_list('role', flat=True).distinct())


class RoleAssignment(models.Model):
    ROLE_CHOICES = [
        ('Mentor', 'Mentor'),
        ('Learner', 'Learner'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    context = models.TextField(blank=True, help_text="Optional context or notes on role")

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        status = "Active" if not self.end_time else "Ended"
        return f"{self.user.username} - {self.role} ({status})"
