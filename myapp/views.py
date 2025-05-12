from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit, Category, Weekday
from .forms import HabitForm, ProfileForm
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm
from django.contrib.auth import logout
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


def welcome_page(request):
    return render(request, 'registration/welcome.html')

def home_page(request):
    today = timezone.now().date()
    habits = Habit.objects.filter(user=request.user)
    habits_today = habits.filter(weekdays__day_of_week=today.weekday()).distinct()
    completed_today = habits_today.filter(completion_date=today)

    return render(request, 'habits/home.html', {
        'habits': habits,
        'habits_today': habits_today,
        'completed_today': completed_today
    })

def toggle_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    habit.toggle_completion()
    return JsonResponse({'success': True})

@login_required
def toggle_habit_completion(request, habit_id):
    if request.method == 'POST':
        habit = get_object_or_404(Habit, id=habit_id, user=request.user)
        habit.completed = not habit.completed
        habit.completion_date = timezone.now().date() if habit.completed else None
        habit.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def add_habit(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            return redirect('dashboard')
    return redirect('dashboard')


#добавление привычки при выборе категории
@login_required
@require_POST
@csrf_exempt
def api_add_habit(request):
    try:
        data = json.loads(request.body)

        name = data.get('name')
        description = data.get('description')
        date_str = data.get('date')
        category_id = data.get('category_id')  # Получаем category_id из запроса
        weekdays = data.get('weekdays', [])  # Получаем дни недели из запроса

        if not name:
            return JsonResponse({'success': False, 'message': 'Название обязательно'}, status=400)

        # Получаем категорию, если она передана в запросе
        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Категория не найдена'}, status=400)

        # Создание привычки
        habit = Habit.objects.create(
            name=name,
            description=description,
            user=request.user,
            category=category,  # Используем полученную категорию
            completed=False,  # Привычка по умолчанию не завершена
        )

        # Устанавливаем дни недели для привычки
        if weekdays:
            for weekday in weekdays:
                try:
                    day = Weekday.objects.get(day_of_week=weekday)
                    habit.weekdays.add(day)
                except Weekday.DoesNotExist:
                    return JsonResponse({'success': False, 'message': f'Некорректный день недели: {weekday}'}, status=400)

        # Если дата указана, устанавливаем completion_date
        if date_str:
            try:
                habit.completion_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                habit.completed = True  # Привычка считается выполненной, если дата установлена
                habit.save()
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Неверный формат даты'}, status=400)

        # Возвращаем успешный ответ с данными о привычке
        return JsonResponse({
            'success': True,
            'habit': {
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'category': habit.category.id if habit.category else None,
                'completion_date': habit.completion_date.strftime('%Y-%m-%d') if habit.completion_date else None,
                'completed': habit.completed,
                'weekdays': [day.day_of_week for day in habit.weekdays.all()]  # Возвращаем выбранные дни недели
            }
        }, status=201)

    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Категория не найдена'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@csrf_exempt
def add_template_habit(request, habit_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            weekdays_ids = data.get('weekdays', [])  # Получаем ID дней недели (например, [1, 3, 5])
            category_id = data.get('category_id')

            if not weekdays_ids:
                return JsonResponse({'error': 'Не указаны дни недели'}, status=400)

            # Получаем шаблон привычки
            template_habit = get_object_or_404(Habit, id=habit_id, is_template=True)
            category = get_object_or_404(Category, id=category_id) if category_id else None

            # Проверяем, не существует ли уже такая привычка
            existing_habit = Habit.objects.filter(
                user=request.user,
                name=template_habit.name,
                category=category,
                is_template=False
            ).first()

            # Получаем объекты Weekday для выбранных дней
            weekdays = Weekday.objects.filter(id__in=weekdays_ids)

            if existing_habit:
                # Обновляем существующую привычку
                existing_habit.weekdays.set(weekdays)  # Используем set для обновления связи
                existing_habit.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Привычка обновлена',
                    'habit_id': existing_habit.id
                })
            else:
                # Создаем новую привычку
                habit = Habit.objects.create(
                    name=template_habit.name,
                    description=template_habit.description,
                    category=category,
                    user=request.user,
                    is_template=False
                )
                habit.weekdays.set(weekdays)  # Сохраняем выбранные дни недели
                habit.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Привычка создана',
                    'habit_id': habit.id
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Неверный метод'}, status=405)

#редактирование привычки при выборе категории
@csrf_exempt
@login_required
def api_update_habit(request):
    try:
        data = json.loads(request.body)

        template_id = data.get('id')
        new_name = data.get('name', '').strip()
        new_description = data.get('description', '').strip()
        category_id = data.get('category_id')

        template = Habit.objects.get(id=template_id, is_template=True)

        # Категория
        category = Category.objects.get(id=category_id) if category_id else None

        # Создаём привычку с новыми данными
        new_habit = Habit.objects.create(
            user=request.user,
            name=new_name if new_name else template.name,
            description=new_description if new_description else template.description,
            category=category,
            is_template=False
        )

        return JsonResponse({'success': True, 'habit_id': new_habit.id})

    except Habit.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Шаблонная привычка не найдена'}, status=404)
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Категория не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


#редактирвоание привычки
@login_required
def edit_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = HabitForm(instance=habit)
    return render(request, 'habits/edit.html', {'form': form})

@login_required
def delete_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method == 'POST':
        habit.delete()
    return redirect('dashboard')

def custom_logout(request):
    logout(request)
    return redirect('/')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'registration/login.html', {'error': 'Неверные данные'})
    return render(request, 'registration/login.html')


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/sign_up.html', {'form': form})


@login_required #////////////////////
def chart_view(request):
    habits = Habit.objects.filter(user=request.user)
    categories = Category.objects.all()

    # Статистика по категориям
    category_stats = [
        {
            'name': category.name,
            'count': habits.filter(category=category).count(),
            'color': get_category_color(category.name.lower())  # ключ — имя категории в нижнем регистре
        }
        for category in categories
    ]

    # Статистика выполнения
    completed_count = habits.filter(completed=True).count()
    not_completed_count = habits.filter(completed=False).count()

    return render(request, 'icons/chart.html', {
        'habits': habits,
        'categories': [(cat.id, cat.name) for cat in categories],  # если нужно для фильтра
        'category_stats': category_stats,
        'completed_count': completed_count,
        'not_completed_count': not_completed_count
    })

@login_required
def dashboard(request):

    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.completed = False  #дефолтное значение
            habit.save()
            return redirect('dashboard')
    else:
        form = HabitForm()

    user_habits = Habit.objects.filter(user=request.user)
    return render(request, 'habits/main_page.html', {'form': form, 'habits': user_habits})


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
                    customuser.profile_picture.delete()  # Удаляем старое фото, если оно есть
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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# @login_required
# def chart_view(request):
#     habits = Habit.objects.filter(user=request.user)
#     categories = Habit.CATEGORY_CHOICES
#
#     # Статистика по категориям
#     category_stats = [
#         {
#             'name': cat[1],
#             'count': habits.filter(category=cat[0]).count(),
#             'color': get_category_color(cat[0])
#         }
#         for cat in categories
#     ]
#
#     # Статистика выполнения
#     completed_count = habits.filter(completed=True).count()
#     not_completed_count = habits.filter(completed=False).count()
#
#     return render(request, 'icons/chart.html', {
#         'habits': habits,
#         'categories': categories,
#         'category_stats': category_stats,
#         'completed_count': completed_count,
#         'not_completed_count': not_completed_count
#     })


def get_category_color(category_name): #//////////////
    color_map = {
        'здоровье': '#FF6384',
        'спорт': '#36A2EB',
        'учёба': '#FFCE56',
        'работа': '#4BC0C0',
        'другое': '#9966FF'
    }
    return color_map.get(category_name, '#C9CBCF')

# получение привычки по категориям
@login_required
def filter_habits_by_category(request, category_param):
    try:
        category = get_object_or_404(Category, id=category_param)
        habits = Habit.objects.filter(category=category, is_template=True)

        data = list(habits.values('id', 'name', 'description', 'is_template'))
        return JsonResponse({'habits': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#переход на след страницу если привычек много
# def paginated_habits(request):
#     page_number = request.GET.get('page', 1)
#     habits = Habit.objects.filter(user=request.user).order_by('-id')  # 🔒 Только привычки пользователя
#     paginator = Paginator(habits, 6)  # 6 привычек на страницу
#
#     page = paginator.get_page(page_number)
#
#     habits_data = [
#         {
#             'id': habit.id,
#             'name': habit.name,
#             'description': habit.description,
#             'completed_today': habit.completed_today,
#         }
#         for habit in page
#     ]
#
#     return JsonResponse({
#         'habits': habits_data,
#         'has_previous': page.has_previous(),
#         'has_next': page.has_next(),
#         'page': page.number,
#         'total_pages': paginator.num_pages,
#     })

from django.contrib.auth import get_user_model

User = get_user_model()
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
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


@login_required
def calendar_view(request):
    # Получаем текущую дату или выбранную пользователем
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
        current_date = datetime(year=year, month=month, day=1)
    except (ValueError, TypeError):
        current_date = timezone.now().replace(day=1)

    prev_month = (current_date - timedelta(days=1)).replace(day=1)
    next_month = (current_date + timedelta(days=32)).replace(day=1)

    import calendar
    cal = calendar.monthcalendar(current_date.year, current_date.month)

    first_day = current_date.replace(day=1)
    last_day = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    habits = Habit.objects.filter(
        Q(user=request.user, completion_date__range=(first_day, last_day)) |
        Q(user=request.user, is_template=True)
    ).distinct()

    habits_by_day = {}
    for habit in habits:
        if habit.completion_date:
            day = habit.completion_date.day
            if day not in habits_by_day:
                habits_by_day[day] = []
            habits_by_day[day].append(habit)

    return render(request, 'habits/calendar.html', {
        'calendar': cal,
        'current_date': current_date,
        'prev_month': prev_month,
        'next_month': next_month,
        'habits_by_day': habits_by_day,
    })

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


