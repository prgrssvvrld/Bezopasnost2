from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_login, name='home'),
    # path('habits/', views.habits, name='habits'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add/', views.add_habit, name='add_habit'),
    path('dashboard/<int:habit_id>/edit/', views.edit_habit, name='edit_habit'),
    path('dashboard/<int:habit_id>/delete/', views.delete_habit, name='delete_habit'),
]