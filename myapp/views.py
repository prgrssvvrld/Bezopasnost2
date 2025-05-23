from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit
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

User = get_user_model()


def welcome_page(request):
    return render(request, 'registration/welcome.html')


def home_page(request):
    return render(request, 'habits/home.html', {

    })

def toggle_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    habit.toggle_completion()
    return JsonResponse({'success': True})

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

# @require_POST
# @login_required
# def toggle_habit_completion(request, habit_id):
#     habit = get_object_or_404(Habit, id=habit_id, user=request.user)
#     data = json.loads(request.body)
#     date_str = data.get('date')
#
#     # Логирование входных данных
#     logger.info(f"Received request to toggle habit completion for habit_id: {habit_id}, date: {date_str}")
#
#     if not date_str:
#         return JsonResponse({'error': 'Date is required'}, status=400)
#
#     try:
#         date = datetime.strptime(date_str, '%Y-%m-%d').date()
#     except ValueError:
#         logger.error(f"Invalid date format: {date_str}")
#         return JsonResponse({'error': 'Invalid date format'}, status=400)
#
#     today = timezone.now().date()
#
#     # Проверяем, что дата не в будущем
#     if date > today:
#         logger.error(f"Attempt to mark habit completion for a future date: {date}")
#         return JsonResponse({'error': 'Нельзя отмечать привычки в будущем'}, status=400)
#
#     # Логика проверки, что привычка запланирована на этот день
#     if date.weekday() not in [s.day_of_week for s in habit.schedule.all()]:
#         logger.error(f"Habit not scheduled for the selected day: {date.weekday()}")
#         return JsonResponse({'error': 'Привычка не запланирована на этот день'}, status=400)
#
#     # Попытка получить или создать запись о выполнении привычки
#     completion, created = HabitCompletion.objects.get_or_create(habit=habit, date=date)
#
#     if created:
#         completed = True
#     else:
#         # Если привычка уже была выполнена, то отменяем выполнение
#         completion.delete()
#         completed = False
#
#     # Логирование результата
#     logger.info(f"Completion status for habit_id {habit_id} on {date}: {completed}")
#
#     return JsonResponse({
#         'completed': completed,
#         'completion_rate': habit.get_completion_rate(),
#         'current_streak': habit.get_current_streak(),
#         'longest_streak': habit.get_longest_streak(),
#     })



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
            try:
                # Валидация пароля
                validate_password(form.cleaned_data['password1'])

                user = form.save()
                login(request, user)
                return redirect('home')
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
@login_required
def calendar_view(request):
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
        current_date = datetime(year=year, month=month, day=1).date()
    except (ValueError, TypeError):
        current_date = timezone.now().date().replace(day=1)

    prev_month = (current_date - timedelta(days=1)).replace(day=1)
    next_month = (current_date + timedelta(days=32)).replace(day=1)

    cal = calendar.monthcalendar(current_date.year, current_date.month)

    first_day = current_date.replace(day=1)
    last_day = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Получаем все привычки пользователя
    habits = Habit.objects.filter(user=request.user)

    # Получаем все выполнения привычек за текущий месяц
    completions = HabitCompletion.objects.filter(
        habit__user=request.user,
        date__gte=first_day,
        date__lte=last_day
    ).select_related('habit')

    # Создаем структуру данных для календаря
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            day_data = {
                'day': day,
                'habits': [],
                'date': current_date.replace(day=day) if day != 0 else None
            }

            if day != 0:
                # Находим привычки, выполненные в этот день
                day_completions = [c for c in completions if c.date.day == day]
                for completion in day_completions:
                    day_data['habits'].append({
                        'id': completion.habit.id,
                        'name': completion.habit.name,
                        'color_class': completion.habit.color_class,
                        'completed': completion.completed,
                        'completion_id': completion.id
                    })

            week_data.append(day_data)
        calendar_data.append(week_data)

    context = {
        'calendar': calendar_data,
        'current_date': current_date,
        'prev_month': prev_month,
        'next_month': next_month,
        'month_name': current_date.strftime('%B %Y'),
        'user_habits': habits,
    }

    return render(request, 'habits/calendar.html', context)


@login_required
def toggle_habit_completion(request, habit_id):
    if request.method == 'POST':
        habit = get_object_or_404(Habit, id=habit_id, user=request.user)

        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = None
        except:
            date = None

        if date:
            new_habit = Habit.objects.create(
                user=request.user,
                name=habit.name,
                description=habit.description,
                category=habit.category,
                completion_date=date,
                completed=True
            )
            return JsonResponse({'success': True, 'habit_id': new_habit.id})

        habit.completed = not habit.completed
        habit.completion_date = timezone.now().date() if habit.completed else None
        habit.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


from django.utils import timezone
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

from django.utils import timezone

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

        # Проверка, чтобы дата не была в будущем
        if selected_date > today:
            return JsonResponse({'success': False, 'error': 'Cannot mark habit for a future date'})

        day_of_week = selected_date.weekday()

        # Проверка, что привычка запланирована на этот день недели
        if not habit.schedule.filter(day_of_week=day_of_week).exists():
            return JsonResponse({'success': False, 'error': 'Habit is not scheduled for this day'})

        completion, created = HabitCompletion.objects.get_or_create(
            habit=habit,
            date=selected_date,
            defaults={'completed': True}
        )

        if not created:
            completion.delete()
            completed = False
        else:
            completed = True

        return JsonResponse({
            'success': True,
            'completed': completed,
            'completion_rate': habit.get_completion_rate(),
            'current_streak': habit.get_current_streak(),
            'longest_streak': habit.get_longest_streak()
        })

    except Habit.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Habit not found'})
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