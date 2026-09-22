from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notifications_list'),
    path('<int:notification_id>/read/', views.notification_read_view, name='notification_read'),
    path('mark-all-read/', views.mark_all_read_view, name='notification_mark_all_read'),
    path('clear-read/', views.clear_read_notifications_view, name='notification_clear_read'),
]
