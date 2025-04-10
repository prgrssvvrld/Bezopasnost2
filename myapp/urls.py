from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.custom_login, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add/', views.add_habit, name='add_habit'),
    #path('dashboard/<int:habit_id>/edit/', views.edit_habit, name='edit_habit'),
    #path('dashboard/<int:habit_id>/delete/', views.delete_habit, name='delete_habit'),
    path('dashboard/chart/', views.chart_view, name='chart'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('habits/<int:habit_id>/toggle/', views.toggle_habit_completion, name='toggle_habit_completion'),

    path('api/habits/category/<int:category_param>/', views.filter_habits_by_category, name='filter_habits_by_category'),
    path('api/habits/add-template/<int:habit_id>/', views.add_template_habit, name='add_template_habit'),
    path('api/habits/create/', views.api_add_habit, name='api_add_habit'),
    path('api/habits/save/', views.api_update_habit, name='api_update_habit'),
    path('habits/<int:habit_id>/delete/', views.delete_habit, name='delete_habit'),
    path('habits/<int:habit_id>/edit/', views.edit_habit, name='edit_habit'),
    path('settings/', views.settings_view, name='settings'),
    path('change-password/', views.settings_view, name='change_password'),


    path('faq/', views.faq_view, name='faq'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)