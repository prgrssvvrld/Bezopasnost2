from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit
from .forms import HabitForm, ProfileForm
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm
from django.contrib.auth import logout
from django.http import JsonResponse
from django.template.defaulttags import register
from django.views.decorators.http import require_GET
from django.urls import reverse

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
            return redirect('dashboard')
        else:
            return render(request, 'registration/login.html', {'error': 'Неверные данные'})
    return render(request, 'registration/login.html')


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('habits')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/sign_up.html', {'form': form})


@login_required
def chart_view(request):
    habits = Habit.objects.filter(user=request.user)

    # Статистика по категориям
    categories = Habit.CATEGORY_CHOICES
    category_counts = [
        habits.filter(category=cat[0]).count() for cat in categories
    ]
    category_labels = [cat[1] for cat in categories]

    # Статистика выполнения
    completed = habits.filter(completed=True).count()
    not_completed = habits.filter(completed=False).count()

    return render(request, 'icons/chart.html', {
        'habits': habits,
        'categories': categories,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'completion_stats': [completed, not_completed]
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


@login_required
def chart_view(request):
    habits = Habit.objects.filter(user=request.user)
    categories = Habit.CATEGORY_CHOICES

    # Статистика по категориям
    category_stats = [
        {
            'name': cat[1],
            'count': habits.filter(category=cat[0]).count(),
            'color': get_category_color(cat[0])
        }
        for cat in categories
    ]

    # Статистика выполнения
    completed_count = habits.filter(completed=True).count()
    not_completed_count = habits.filter(completed=False).count()

    return render(request, 'icons/chart.html', {
        'habits': habits,
        'categories': categories,
        'category_stats': category_stats,
        'completed_count': completed_count,
        'not_completed_count': not_completed_count
    })


def get_category_color(category):
    colors = {
        'health': '#FF6384',
        'sport': '#36A2EB',
        'study': '#FFCE56',
        'work': '#4BC0C0',
        'other': '#9966FF'
    }
    return colors.get(category, '#C9CBCF')