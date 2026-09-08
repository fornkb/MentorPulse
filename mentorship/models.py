from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Mentorship(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active Mentorship'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_mentorships')
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learner_mentorships')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    goals = models.TextField(help_text="Target learning objectives and focus areas")
    is_priority = models.BooleanField(default=False, help_text="Priority queue status")

    class Meta:
        ordering = ['-is_priority', '-id']

    def __str__(self):
        return f"{self.learner.username} -> {self.mentor.username} ({self.status})"

    def can_access(self, user):
        """Check whether a user is an authorized participant or admin."""
        return user.is_authenticated and (user == self.mentor or user == self.learner or user.is_staff)

    @property
    def is_active(self):
        return self.status == 'ACTIVE'

    @property
    def is_completed(self):
        return self.status == 'COMPLETED'


class Progress(models.Model):
    mentorship = models.OneToOneField(Mentorship, on_delete=models.CASCADE, related_name='progress')
    completion_pct = models.FloatField(default=0.0)
    skill_score = models.FloatField(default=0.0)
    tasks = models.TextField(blank=True)

    def __str__(self):
        return f"Progress for Mentorship #{self.mentorship_id}: {self.completion_pct}%"

    def recalculate(self):
        """
        Dynamically calculate progress percentage based on:
        - Completed milestones: 70% weight
        - Completed sessions: 30% weight
        """
        if self.mentorship.status == 'COMPLETED':
            self.completion_pct = 100.0
            self.save()
            return self.completion_pct

        total_milestones = self.mentorship.milestones.count()
        completed_milestones = self.mentorship.milestones.filter(is_completed=True).count()

        total_sessions = self.mentorship.sessions.count()
        completed_sessions = self.mentorship.sessions.filter(is_completed=True).count()

        milestone_score = 0.0
        session_score = 0.0

        if total_milestones > 0 and total_sessions > 0:
            milestone_score = (completed_milestones / total_milestones) * 70.0
            session_score = (completed_sessions / total_sessions) * 30.0
            total_pct = milestone_score + session_score
        elif total_milestones > 0:
            total_pct = (completed_milestones / total_milestones) * 100.0
        elif total_sessions > 0:
            total_pct = (completed_sessions / total_sessions) * 100.0
        else:
            total_pct = 0.0

        self.completion_pct = round(min(100.0, max(0.0, total_pct)), 1)
        self.save()
        return self.completion_pct


class Session(models.Model):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateTimeField()
    meeting_link = models.URLField(blank=True, help_text="Google Meet or Zoom URL")
    notes = models.TextField(blank=True, help_text="Meeting agenda or follow-up notes")
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

    def __str__(self):
        status = "Completed" if self.is_completed else "Scheduled"
        return f"Session on {self.date.strftime('%b %d, %Y')} ({status})"


class Milestone(models.Model):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        status = "Done" if self.is_completed else "Incomplete"
        return f"{self.title} ({status})"


class Resource(models.Model):
    TYPE_CHOICES = [
        ('LINK', 'Web Link'),
        ('FILE', 'File Upload (<=10MB)'),
        ('NOTE', 'Note / Markdown'),
    ]

    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='resources')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='LINK')
    content = models.TextField(blank=True, help_text="URL for link or text for note")
    file = models.FileField(upload_to='resources/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.title}"


class DiscussionPost(models.Model):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='discussion_posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} at {self.created_at.strftime('%b %d, %H:%M')}"
