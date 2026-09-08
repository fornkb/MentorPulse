from django.contrib import admin
from .models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


class ProgressInline(admin.StackedInline):
    model = Progress
    can_delete = False


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'learner', 'mentor', 'status', 'is_priority', 'start_date', 'end_date')
    list_filter = ('status', 'is_priority', 'start_date')
    search_fields = ('learner__username', 'mentor__username', 'goals')
    inlines = [ProgressInline, MilestoneInline, SessionInline]


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'completion_pct', 'skill_score')
    search_fields = ('mentorship__learner__username', 'mentorship__mentor__username')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'date', 'is_completed', 'meeting_link')
    list_filter = ('is_completed', 'date')
    search_fields = ('mentorship__learner__username', 'mentorship__mentor__username', 'notes')


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'title', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)
    search_fields = ('mentorship__learner__username', 'mentorship__mentor__username', 'title')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'type', 'uploaded_by', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('title', 'content')


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'mentorship', 'created_at')
    search_fields = ('author__username', 'text')
