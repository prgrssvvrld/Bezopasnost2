from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit, CustomUser
from .forms import HabitForm, ProfileForm, CustomUserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseBadRequest
from django.template.defaulttags import register
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils import timezone
from datetime import date, timedelta, datetime
from calendar import monthrange
from django.http import JsonResponse
from django.contrib import messages
from .models import HabitCompletion

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from .models import Habit, HabitSchedule
from django.views.decorators.http import require_GET
from datetime import datetime
from datetime import timedelta
import json
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def welcome_page(request):
    return render(request, 'registration/welcome.html')


def verify_code(request):
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email, verification_code=code)

            # Проверка срока действия кода (например, 10 минут)
            if (timezone.now() - user.verification_code_created_at) > timedelta(minutes=10):
                messages.error(request, 'Срок действия кода истёк. Запросите новый.')
                return redirect('sign_up')

            user.is_user_verified = True
            user.is_active = True
            user.save()

            login(request, user)
            messages.success(request, 'Почта успешно подтверждена!')
            return redirect('home')

        except CustomUser.DoesNotExist:
            messages.error(request, 'Неверный код подтверждения')

    return render(request, 'registration/verify_code.html')
def home_page(request):
    user = request.user
    today = timezone.now().date()
    weekday = today.weekday()  # 0 = понедельник

    habits = Habit.objects.filter(user=user)
    habits_today = habits.filter(schedule__day_of_week=weekday).distinct()
    streaks = [habit.get_current_streak() for habit in habits]
    average_streak = round(sum(streaks) / len(streaks)) if streaks else 0

    completed_today = HabitCompletion.objects.filter(
        habit__in=habits_today, date=today, completed=True
    ).values_list('habit_id', flat=True)

    context = {
        'habits': habits,
        'habits_today': habits_today,
        'completed_today': completed_today,
        'average_streak': average_streak,
    }

    return render(request, 'habits/home.html', context)

# def toggle_habit(request, habit_id):
#     habit = get_object_or_404(Habit, id=habit_id, user=request.user)
#     habit.toggle_completion()
#     return JsonResponse({'success': True})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_habit(request):
    try:
        data = json.loads(request.body)
        user = request.user

        habit_id = data.get('habit_id')
        name = data.get('name')
        category = data.get('category')
        description = data.get('description', '')
        days_goal = int(data.get('days_goal', 30))
        reminder = data.get('reminder', False)
        color_class = data.get('color_class')
        schedule_days = data.get('schedule_days', [])

        # Создание или обновление привычки
        if habit_id:
            habit = Habit.objects.get(id=habit_id, user=user)
            habit.name = name
            habit.category = category
            habit.description = description
            habit.days_goal = days_goal
            habit.reminder = reminder
            habit.color_class = color_class
            habit.save()
        else:
            habit = Habit.objects.create(
                user=user,
                name=name,
                category=category,
                description=description,
                days_goal=days_goal,
                reminder=reminder,
                color_class=color_class
            )

        # Обновляем дни расписания
        HabitSchedule.objects.filter(habit=habit).delete()
        for day in schedule_days:
            HabitSchedule.objects.create(habit=habit, day_of_week=int(day))

        return JsonResponse({'success': True, 'habit': serialize_habit(habit)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def serialize_habit(habit, date=None):
    return {
        'id': habit.id,
        'name': habit.name,
        'category': habit.category,
        'category_display': habit.get_category_display(),
        'description': habit.description,
        'days_goal': habit.days_goal,
        'reminder': habit.reminder,
        'color_class': habit.color_class,
        'schedule_days': list(habit.schedule.values_list('day_of_week', flat=True)),
        'completed': habit.is_completed_on(date),  # ✅ проверка на конкретную дату!
        'is_completed_today': habit.is_completed_on(date) if date else habit.is_completed_today(),
        'get_completion_rate': habit.get_completion_rate(),
        'completion_rate': habit.get_completion_rate(),
        'current_streak': habit.get_current_streak(),
        'longest_streak': habit.get_longest_streak(),
    }

@require_GET
def get_all_habits(request):
    habits = Habit.objects.filter(user=request.user).prefetch_related('schedule')
    habits_data = []

    for habit in habits:
        habits_data.append({
            'id': habit.id,
            'name': habit.name,
            'category': habit.category,
            'category_display': habit.get_category_display(),
            'description': habit.description,
            'days_goal': habit.days_goal,
            'color_class': habit.color_class,
            'schedule_days': [s.day_of_week for s in habit.schedule.all()],
            'reminder': habit.reminder
        })

    return JsonResponse({'success': True, 'habits':[serialize_habit(h) for h in habits]})

@require_GET
def get_habits_by_day(request):
    day = request.GET.get('day')
    date_str = request.GET.get('date')

    if not day:
        return JsonResponse({'success': False, 'error': 'Day parameter is required'})

    try:
        day = int(day)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid day format'})

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'})

    habits = Habit.objects.filter(
        user=request.user,
        schedule__day_of_week=day
    ).distinct().prefetch_related('schedule')

    habits_data = []
    for habit in habits:
        habit_data = serialize_habit(habit, date=selected_date)
        habit_data['is_completed_today'] = habit.is_completed_on(selected_date)
        habits_data.append(habit_data)

    return JsonResponse({'success': True, 'habits': habits_data})

# //////////////////////////////////
@login_required
@require_POST
def add_habit(request):
    try:
        data = json.loads(request.body)
        habit = Habit.objects.create(
            user=request.user,
            name=data['name'],
            category=data['category'],
            description=data.get('description', ''),
            days_goal=data.get('days_goal', 30),
            color_class=data.get('color_class', 'bg-gray-100 text-gray-800'),
            reminder=data.get('reminder', False),
        )
        HabitSchedule.objects.bulk_create([
            HabitSchedule(habit=habit, day_of_week=day) for day in data.get('repeat_days', [])
        ])
        return JsonResponse({'status': 'success', 'habit': _habit_summary(habit)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# @login_required
# def get_habits(request):
#     habits = Habit.objects.filter(user=request.user).prefetch_related('schedule')
#     return JsonResponse({'habits': [_habit_full(h) for h in habits]})

#////////////////////////
@login_required
def get_habits_for_day(request):
    # Получаем день недели из параметра запроса (по умолчанию воскресенье - 0)
    day_of_week = int(request.GET.get('day', 0))

    # Получаем привычки, связанные с этим днем недели
    habits = Habit.objects.filter(user=request.user, schedule__day_of_week=day_of_week)

    # Сериализуем привычки и возвращаем их
    habits_data = [serialize_habit(habit) for habit in habits]

    return JsonResponse({'success': True, 'habits': habits_data})


@login_required
@require_http_methods(["POST"])
def delete_habit(request, id):
    habit = Habit.objects.filter(id=id, user=request.user).first()
    if habit:
        habit.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Habit not found'}, status=404)



@login_required
@require_http_methods(["POST"])
def update_habit(request, id):
    try:
        data = json.loads(request.body)
        habit = get_object_or_404(Habit, id=id, user=request.user)

        # Обновление основных полей
        for field in ['name', 'category', 'description', 'days_goal', 'color_class', 'reminder']:
            if field in data:
                setattr(habit, field, data[field])
        habit.save()

        # Обновление расписания
        new_days = set(data.get('repeat_days', []))
        existing_days = set(habit.schedule.values_list('day_of_week', flat=True))

        # Добавляем новые дни
        for day in new_days - existing_days:
            HabitSchedule.objects.create(habit=habit, day_of_week=day)

        # Удаляем старые дни, которых больше нет
        habit.schedule.filter(day_of_week__in=existing_days - new_days).delete()

        return JsonResponse({'status': 'success', 'habit': _habit_summary(habit)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def get_habit(request, id):
    habit = Habit.objects.filter(id=id, user=request.user).prefetch_related('schedule').first()
    if habit:
        return JsonResponse(_habit_full(habit))
    return JsonResponse({'status': 'error', 'message': 'Habit not found'}, status=404)

@login_required
@require_POST
def track_habit(request, pk):
    try:
        # Заглушка: в будущем можно реализовать HabitCompletion
        habit = get_object_or_404(Habit, id=pk, user=request.user)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


import logging

logger = logging.getLogger(__name__)



# ———————————————————————
# 🔧 Вспомогательные функции
# ———————————————————————

def _habit_summary(habit):
    return {
        'id': habit.id,
        'name': habit.name,
        'category': habit.get_category_display(),
        'color_class': habit.color_class,
        'days_goal': habit.days_goal,
    }


def _habit_full(habit):
    return {
        'id': habit.id,
        'name': habit.name,
        'category': habit.category,
        'description': habit.description,
        'color_class': habit.color_class,
        'days_goal': habit.days_goal,
        'reminder': habit.reminder,
        'repeat_days': list(habit.schedule.values_list('day_of_week', flat=True)),
        'schedule_days': [s.day_of_week for s in habit.schedule.all()],
    }

def custom_logout(request):
    logout(request)
    return redirect('/')


def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Проверяем, были ли недавние попытки входа
        last_failed_attempt = request.session.get('last_failed_attempt')
        if last_failed_attempt:
            elapsed = timezone.now().timestamp() - float(last_failed_attempt)
            if elapsed < 5:  # 5 секунд таймаут
                remaining_time = 5 - int(elapsed)
                messages.error(request, f'Пожалуйста, подождите {remaining_time} секунд перед следующей попыткой')
                return render(request, 'registration/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            # Сохраняем время неудачной попытки
            request.session['last_failed_attempt'] = timezone.now().timestamp()
            messages.error(request, 'Неверное имя пользователя или пароль')
            return render(request, 'registration/login.html')
    return render(request, 'registration/login.html')


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Сохраняем время создания кода
            user.verification_code_created_at = timezone.now()
            user.save()

            # Перенаправляем на страницу ввода кода
            return redirect(f'/verify-code/?email={user.email}')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/sign_up.html', {'form': form})


@login_required
def chart_view(request):
    habits = Habit.objects.filter(user=request.user).order_by('-created_at')

    # Пагинация - 10 привычек на страницу
    paginator = Paginator(habits, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Рассчитываем статистику по всем привычкам (не только текущей странице)
    category_stats = []
    for category in Habit.CATEGORY_CHOICES:
        count = habits.filter(category=category[0]).count()
        if count > 0:
            color = get_category_color(category[0])
            category_stats.append({
                'name': category[1],  # Отображаемое имя
                'count': count,
                'color': color
            })

    # Статистика выполнения (по всем привычкам)
    completed_count = sum(1 for habit in habits if habit.is_completed_today())
    not_completed_count = habits.count() - completed_count

    return render(request, 'icons/chart.html', {
        'page_obj': page_obj,  # Передаем объект страницы вместо всех привычек
        'categories': Habit.CATEGORY_CHOICES,
        'category_stats': category_stats,
        'completed_count': completed_count,
        'not_completed_count': not_completed_count,
        'total_habits_count': habits.count()  # Общее количество привычек для информации
    })


def get_category_color(category_name):
    color_map = {
        'health': 'rgba(75, 192, 192, 0.7)',
        'productivity': 'rgba(54, 162, 235, 0.7)',
        'learning': 'rgba(255, 206, 86, 0.7)',
        'relationships': 'rgba(153, 102, 255, 0.7)',
        'finance': 'rgba(255, 99, 132, 0.7)'
    }
    return color_map.get(category_name.lower(), 'rgba(201, 203, 207, 0.7)')


def get_category_color(category_name):
    color_map = {
        'health': 'rgba(75, 192, 192, 0.7)',
        'productivity': 'rgba(54, 162, 235, 0.7)',
        'learning': 'rgba(255, 206, 86, 0.7)',
        'relationships': 'rgba(153, 102, 255, 0.7)',
        'finance': 'rgba(255, 99, 132, 0.7)'
    }
    return color_map.get(category_name.lower(), 'rgba(201, 203, 207, 0.7)')


@login_required
def dashboard(request):
    today = timezone.now().date()
    weekday = today.weekday()

    habits = Habit.objects.filter(user=request.user).prefetch_related('schedule')
    daily_habits = habits.filter(schedule__day_of_week=weekday).distinct()

    for habit in daily_habits:
        habit.is_completed_today = habit.is_completed_today()
        habit.completion_rate = habit.get_completion_rate()
        habit.current_streak = habit.get_current_streak()
        habit.longest_streak = habit.get_longest_streak()

    return render(request, 'habits/main_page.html', {
        'habits': habits,
        'daily_habits': daily_habits,
        'today': today.strftime('%Y-%m-%d'),
    })
@login_required
def profile_view(request):
    return render(request, 'habits/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)

        if 'delete_photo' in request.POST:
            if request.user.profile_picture:
                request.user.profile_picture.delete()
                request.user.profile_picture = None
                request.user.save()
            return redirect('profile')

        if form.is_valid():
            customuser = form.save()

            if 'profile_picture' in request.FILES:
                if customuser.profile_picture:
                    customuser.profile_picture.delete()
                customuser.profile_picture = request.FILES['profile_picture']
                customuser.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'habits/edit_profile.html', {'form': form})


@login_required
def faq_view(request):
    faq_items = [
        {
            'question': 'Зачем это приложение?',
            'answer': 'Это приложение помогает вам формировать и отслеживать полезные привычки, анализировать ваш прогресс и мотивирует на достижение целей.'
        },
        {
            'question': 'Как добавить привычку?',
            'answer': 'На главной странице заполните форму: выберите категорию, укажите название и описание привычки, затем нажмите "Добавить привычку".'
        },
        {
            'question': 'Как отметить привычку как выполненную?',
            'answer': 'На странице статистики (графики) нажмите на чекбокс рядом с привычкой. Вы можете изменить статус выполнения в любое время.'
        },
        {
            'question': 'Как работает анализ прогресса?',
            'answer': 'Приложение анализирует количество выполненных привычек по категориям и дням недели, показывая ваш прогресс в виде наглядных графиков.'
        }
    ]
    return render(request, 'habits/faq.html', {'faq_items': faq_items})





@login_required
def filter_habits_by_category(request, category_param):
    try:
        category = get_object_or_404(Category, id=category_param)
        habits = Habit.objects.filter(category=category, is_template=True)

        data = list(habits.values('id', 'name', 'description', 'is_template'))
        return JsonResponse({'habits': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


@login_required
def settings_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)

        if 'old_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно обновлен!')
                return redirect('settings')
            else:
                messages.error(request, 'Ошибка при обновлении пароля.')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Профиль успешно обновлён.')
                return redirect('settings')
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'icons/settings.html', {
        'user_form': user_form,
        'password_form': password_form
    })


from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .models import Habit

import calendar
# views.py

@require_POST
@login_required
def toggle_completion(request, habit_id):
    try:
        habit = Habit.objects.get(id=habit_id, user=request.user)

        date_str = request.POST.get('date')
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Missing date parameter'})

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})

        today = timezone.now().date()

        # Нельзя отмечать будущее
        if selected_date > today:
            return JsonResponse({'success': False, 'error': 'Нельзя отмечать в будущем'})

        # Проверка, запланирована ли привычка на этот день
        if not habit.schedule.filter(day_of_week=selected_date.weekday()).exists():
            return JsonResponse({'success': False, 'error': 'Привычка не запланирована на этот день'})

        # Получаем или создаем объект HabitCompletion
        completion, _ = HabitCompletion.objects.get_or_create(
            habit=habit,
            date=selected_date
        )

        # Переключаем статус
        completion.completed = not completion.completed
        completion.save()

        return JsonResponse({
            'success': True,
            'completed': completion.completed,
            'completion_rate': habit.get_completion_rate(),
            'current_streak': habit.get_current_streak(),
            'longest_streak': habit.get_longest_streak()
        })

    except Habit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Привычка не найдена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from django.utils import timezone
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

from django.utils import timezone

@require_POST
@login_required
def toggle_habit_completion(request, habit_id):
    try:
        habit = Habit.objects.get(id=habit_id, user=request.user)

        date_str = request.POST.get('date')
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Missing date parameter'})

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})

        today = timezone.now().date()
        if selected_date > today:
            return JsonResponse({'success': False, 'error': 'Нельзя отмечать в будущем'})

        if not habit.schedule.filter(day_of_week=selected_date.weekday()).exists():
            return JsonResponse({'success': False, 'error': 'Привычка не запланирована на этот день'})

        completion, created = HabitCompletion.objects.get_or_create(
            habit=habit,
            date=selected_date
        )

        # ✅ Явно устанавливаем completed = True при создании
        if created:
            completion.completed = True
        else:
            completion.completed = not completion.completed

        completion.save()

        return JsonResponse({
            'success': True,
            'completed': completion.completed,
            'completion_rate': habit.get_completion_rate(),
            'current_streak': habit.get_current_streak(),
            'longest_streak': habit.get_longest_streak()
        })

    except Habit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Привычка не найдена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


#страница трекера привычек
@login_required
def habit_tracker(request):
    # Получаем все привычки текущего пользователя
    habits = Habit.objects.filter(user=request.user).prefetch_related('completions')

    # Для каждой привычки добавляем данные о выполнении за последние 30 дней
    for habit in habits:
        habit.completion_days = habit.get_completion_days()

    context = {
        'habits': habits,
        'total_habits': habits.count(),
        'today': timezone.now().date(),
    }
    return render(request, 'tracker/tracker.html', context)


@login_required
@require_POST
def mark_habit_completion(request):
    habit_id = request.POST.get('habit_id')
    date_str = request.POST.get('completion_date')

    try:
        habit = Habit.objects.get(id=habit_id, user=request.user)
        completion_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()

        # Проверяем, что дата не в будущем
        if completion_date > timezone.now().date():
            return JsonResponse({'success': False, 'error': 'Дата не может быть в будущем'})

        # Создаем или обновляем запись о выполнении
        completion, created = HabitCompletion.objects.get_or_create(
            habit=habit,
            date=completion_date,
            defaults={'completed': True}
        )

        if not created:
            completion.completed = True
            completion.save()

        return JsonResponse({'success': True})

    except Habit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Привычка не найдена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_completion_days(self, days_to_show=30):
    """Возвращает список дней с информацией о выполнении привычки"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days_to_show - 1)

    # Создаем список всех дней в периоде
    date_list = [start_date + timedelta(days=x) for x in range(days_to_show)]

    # Получаем выполненные дни
    completed_dates = set(self.completions.filter(
        date__gte=start_date,
        date__lte=today
    ).values_list('date', flat=True))

    # Формируем результат
    return [{
        'date': date,
        'completed': date in completed_dates
    } for date in date_list]


#календарь
@login_required
def calendar_view(request):
    today = timezone.now().date()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    # Корректировка месяцев при переходе через год
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    first_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    last_date = date(year, month, last_day)

    # Получаем привычки пользователя
    habits = Habit.objects.filter(user=request.user).prefetch_related('schedule')

    # Создаем календарь
    calendar_days = []
    current_date = first_date

    # Определяем день недели для первого дня месяца (0=Пн, 6=Вс)
    first_day_weekday = first_date.weekday()

    # Добавляем дни предыдущего месяца (чтобы календарь начинался с Пн)
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    _, prev_last_day = monthrange(prev_year, prev_month)
    for d in range(first_day_weekday):
        day = prev_last_day - (first_day_weekday - d - 1)
        calendar_days.append({
            'date': date(prev_year, prev_month, day),
            'current_month': False,
            'habits': []
        })

    # Добавляем дни текущего месяца
    while current_date <= last_date:
        day_of_week = current_date.weekday()

        # Фильтруем привычки по дате создания и по дате в пределах days_goal
        day_habits = []
        for habit in habits:
            # Проверяем, что привычка запланирована на этот день недели
            if any(schedule.day_of_week == day_of_week for schedule in habit.schedule.all()):
                # Привычка должна быть создана до этого дня
                if habit.created_at and habit.created_at.date() <= current_date:
                    # Проверяем, не вышли ли за цель по дням (days_goal)
                    # Собираем все даты, когда привычка должна выполняться, начиная с created_at
                    scheduled_days = sorted([s.day_of_week for s in habit.schedule.all()])
                    # Считаем, сколько таких дней прошло с created_at до current_date включительно
                    # Для этого перебираем даты с created_at, выбираем только подходящие дни недели,
                    # считаем, сколько таких дней не превышает days_goal

                    # Считаем количество запланированных дней от created_at до current_date
                    count_days = 0
                    check_date = habit.created_at.date()
                    while check_date <= current_date:
                        if check_date.weekday() in scheduled_days:
                            count_days += 1
                        check_date += timedelta(days=1)

                    if count_days <= habit.days_goal:
                        day_habits.append(habit)

        calendar_days.append({
            'date': current_date,
            'current_month': True,
            'habits': day_habits,
            'is_today': current_date == today
        })
        current_date += timedelta(days=1)

    # Добавляем дни следующего месяца, чтобы заполнить до 6 недель
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    while len(calendar_days) % 7 != 0:
        calendar_days.append({
            'date': date(next_year, next_month, len(calendar_days) % 7 + 1),
            'current_month': False,
            'habits': []
        })

    # Разбиваем на недели (Пн-Вс)
    weeks = [calendar_days[i:i + 7] for i in range(0, len(calendar_days), 7)]

    # Привычки на сегодня
    today_weekday = today.weekday()
    today_habits = [habit for habit in habits if any(schedule.day_of_week == today_weekday for schedule in habit.schedule.all())]

    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }

    return render(request, 'habits/calendar.html', {
        'month_names': month_names,
        'weeks': weeks,
        'today_habits': today_habits,
        'all_habits': habits,
        'current_month': month,
        'current_year': year,
        'today': today,
        'weekday_names': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    })



from django.utils.dateparse import parse_date


@login_required
def habits_by_date(request):
    """
    Возвращает привычки пользователя, запланированные на конкретную дату,
    с учётом days_goal и даты создания.
    """
    date_str = request.GET.get('date')
    target_date = parse_date(date_str)
    if not target_date:
        return JsonResponse({'error': 'Invalid date'}, status=400)

    weekday = target_date.weekday()  # 0 = Пн … 6 = Вс

    habits_qs = (
        Habit.objects
        .filter(
            user=request.user,
            created_at__date__lte=target_date,
            schedule__day_of_week=weekday
        )
        .distinct()
        .prefetch_related('schedule')
    )

    results = []
    for habit in habits_qs:
        scheduled_days = list(habit.schedule.values_list('day_of_week', flat=True))

        passed = 0
        current = habit.created_at.date()

        while current <= target_date:
            if current.weekday() in scheduled_days:
                passed += 1
            current += timedelta(days=1)

        if passed <= habit.days_goal or target_date == habit.created_at.date():
            results.append({
                'id': habit.id,
                'name': habit.name,
                'category': habit.category,
                'description': habit.description,
                'completed': habit.is_completed_on(target_date),
                'schedule_days': list(habit.schedule.values_list('day_of_week', flat=True)),
                'date': target_date.isoformat(),
                'completion_rate': habit.get_completion_rate(),
                'current_streak': habit.get_current_streak(),
                'longest_streak': habit.get_longest_streak()
            })

    return JsonResponse(results, safe=False)
