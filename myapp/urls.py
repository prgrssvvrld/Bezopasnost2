from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.custom_login, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add/', views.add_habit, name='add_habit'),
    path('dashboard/<int:habit_id>/edit/', views.edit_habit, name='edit_habit'),
    path('dashboard/<int:habit_id>/delete/', views.delete_habit, name='delete_habit'),
    path('dashboard/chart/', views.chart_view, name='chart'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('habits/<int:habit_id>/toggle/', views.toggle_habit_completion, name='toggle_habit_completion'),
    path('faq/', views.faq_view, name='faq'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)