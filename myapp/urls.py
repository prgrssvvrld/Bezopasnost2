from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_login, name='home'),
    # path('habits/', views.habits, name='habits'),
    path('dashboard/', views.dashboard, name='dashboard'),
]