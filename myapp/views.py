from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit
from .forms import HabitForm

def home(request):
    return redirect('habits')
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Перенаправление на страницу входа после регистрации
    else:
        form = UserCreationForm()
    return render(request, 'registration/sign_up.html', {'form': form})
@login_required
def habits(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user  # Привязываем привычку к текущему пользователю
            habit.save()
            return redirect('habits')
    else:
        form = HabitForm()

    # Получаем привычки текущего пользователя
    user_habits = Habit.objects.filter(user=request.user)
    return render(request, 'habits/habits.html', {'form': form, 'habits': user_habits})
