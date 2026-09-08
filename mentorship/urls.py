from django.urls import path
from . import views

urlpatterns = [
    path('', views.mentorship_list_view, name='mentorship_list'),
    path('request/<int:mentor_id>/', views.request_mentorship_view, name='mentorship_request'),
    path('<int:mentorship_id>/', views.mentorship_workspace_view, name='mentorship_workspace'),
    path('<int:mentorship_id>/accept/', views.accept_mentorship_view, name='mentorship_accept'),
    path('<int:mentorship_id>/reject/', views.reject_mentorship_view, name='mentorship_reject'),
    path('<int:mentorship_id>/cancel/', views.cancel_mentorship_view, name='mentorship_cancel'),
    path('<int:mentorship_id>/complete/', views.mentorship_complete_view, name='mentorship_complete'),
    path('<int:mentorship_id>/certificate/', views.certificate_view, name='mentorship_certificate'),
    path('<int:mentorship_id>/sessions/add/', views.session_add_view, name='session_add'),
    path('sessions/<int:session_id>/toggle/', views.session_toggle_view, name='session_toggle'),
    path('<int:mentorship_id>/milestones/add/', views.milestone_add_view, name='milestone_add'),
    path('milestones/<int:milestone_id>/toggle/', views.milestone_toggle_view, name='milestone_toggle'),
    path('<int:mentorship_id>/resources/add/', views.resource_add_view, name='resource_add'),
    path('<int:mentorship_id>/discussions/add/', views.discussion_post_view, name='discussion_post'),
]
