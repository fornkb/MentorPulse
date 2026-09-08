from django.contrib import admin
from .models import Skill, Profile, RoleAssignment


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('category', 'name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'availability', 'skill_score')
    list_filter = ('experience_level', 'availability')
    search_fields = ('user__username', 'user__email', 'bio', 'goals')
    filter_horizontal = ('skills',)


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'start_time', 'end_time', 'is_active')
    list_filter = ('role', 'start_time')
    search_fields = ('user__username', 'context')
    ordering = ('-start_time',)

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        return obj.end_time is None
