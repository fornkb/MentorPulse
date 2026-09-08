from django.urls import path
from . import views

urlpatterns = [
    path('', views.mentor_directory_view, name='mentor_list'),
    path('<int:user_id>/', views.mentor_detail_view, name='mentor_detail'),
]
