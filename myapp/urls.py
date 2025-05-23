from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.welcome_page, name='welcome'),
    path('login/', views.custom_login, name='login'),
    # path('signup/', views.signup, name='sign_up'),
    # path('logout/', views.custom_logout, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/add/', views.add_habit, name='add_habit'),
    path('home/', views.home_page, name='home'),

    path('habits/<int:habit_id>/toggle/', views.toggle_habit, name='toggle_habit'),

    #path('dashboard/<int:habit_id>/edit/', views.edit_habit, name='edit_habit'),
    #path('dashboard/<int:habit_id>/delete/', views.delete_habit, name='delete_habit'),
    path('dashboard/chart/', views.chart_view, name='chart'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('habits/<int:habit_id>/toggle/', views.toggle_habit_completion, name='toggle_habit_completion'),
    path('api/habits/category/<int:category_param>/', views.filter_habits_by_category, name='filter_habits_by_category'),

#настройки
    path('settings/', views.settings_view, name='settings'),
    path('change-password/', views.settings_view, name='change_password'),

#faq
    path('faq/', views.faq_view, name='faq'),

#новые
    path('habits/', views.dashboard, name='habits'),
    path('habits/save/', views.save_habit, name='save_habit'),
    path('habits/get_all/', views.get_all_habits, name='get_all_habits'),
    path('habits/get_by_day/', views.get_habits_by_day, name='get_habits_by_day'),
    path('habits/delete/<int:id>/', views.delete_habit, name='delete_habit'),
    path('habits/update/<int:id>/', views.update_habit, name='update_habit'),
    path('habits/get/<int:id>/', views.get_habit, name='get_habit'),
    path('api/toggle-completion/<int:habit_id>/', views.toggle_completion, name='toggle_completion'),

#календарь
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/habits/by-date/', views.habits_by_date, name='habits_by_date'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)