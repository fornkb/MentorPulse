from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.wallet_view, name='wallet'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('badges/', views.badges_view, name='badges'),
    path('feedback/<int:mentorship_id>/', views.feedback_submit_view, name='feedback_submit'),
]
