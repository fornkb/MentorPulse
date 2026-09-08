from django.contrib import admin
from .models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reason', 'context', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('user__username', 'context')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'given_by', 'given_to', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('given_by__username', 'given_to__username', 'comment')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon')
    list_filter = ('category',)
    search_fields = ('name', 'description')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_date')
    search_fields = ('user__username', 'badge__name')


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('rank', 'user', 'score', 'updated_at')
    ordering = ('rank',)
    search_fields = ('user__username',)
