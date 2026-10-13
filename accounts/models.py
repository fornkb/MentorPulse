from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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
    learning_skills = models.ManyToManyField(Skill, blank=True, related_name='learning_profiles')
    timezone = models.CharField(max_length=64, default='UTC')
    portfolio_url = models.URLField(blank=True)
    mentor_capacity = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(50)])
    mentor_verified = models.BooleanField(default=False)
    verification_requested = models.BooleanField(default=False)
    verification_evidence = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
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
        return list(self.user.role_assignments.filter(end_time__isnull=True).order_by('role').values_list('role', flat=True).distinct())


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


class SavedMentor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_mentors')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'mentor'], name='unique_saved_mentor')]


class AvailabilitySlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability_slots')
    weekday = models.PositiveSmallIntegerField(choices=list(enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])))
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start_time']
        constraints = [models.CheckConstraint(condition=models.Q(end_time__gt=models.F('start_time')), name='availability_end_after_start')]

    def __str__(self):
        return f'{self.get_weekday_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}'


class UserReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=40, choices=[('CONDUCT', 'Inappropriate conduct'), ('SPAM', 'Spam'), ('PROFILE', 'Misleading profile'), ('OTHER', 'Other')])
    details = models.TextField(max_length=4000)
    status = models.CharField(max_length=20, default='OPEN', choices=[('OPEN', 'Open'), ('REVIEWING', 'Under review'), ('RESOLVED', 'Resolved')])
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
