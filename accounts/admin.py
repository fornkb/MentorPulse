from django.contrib import admin
from .models import Skill, Profile, RoleAssignment, AvailabilitySlot, UserReport, SavedMentor


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('category', 'name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'mentor_verified', 'verification_requested', 'email_verified', 'skill_score')
    list_filter = ('verification_requested', 'mentor_verified', 'email_verified', 'experience_level', 'availability')
    search_fields = ('user__username', 'user__email', 'bio', 'goals')
    filter_horizontal = ('skills', 'learning_skills')
    actions = ['approve_verification', 'decline_verification']

    @admin.action(description='Approve requested mentor verification')
    def approve_verification(self, request, queryset):
        queryset.filter(verification_requested=True).update(mentor_verified=True, verification_requested=False)

    @admin.action(description='Decline requested mentor verification')
    def decline_verification(self, request, queryset):
        queryset.update(mentor_verified=False, verification_requested=False)


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'start_time', 'end_time', 'is_active')
    list_filter = ('role', 'start_time')
    search_fields = ('user__username', 'context')
    ordering = ('-start_time',)

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        return obj.end_time is None


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported_user', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason')
    search_fields = ('reporter__username', 'reported_user__username', 'details')
    readonly_fields = ('reporter', 'reported_user', 'reason', 'details', 'created_at')


admin.site.register(AvailabilitySlot)
admin.site.register(SavedMentor)
