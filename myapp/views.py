from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Habit
from .forms import HabitForm
from django.contrib.auth import authenticate, login
#на регистрации пользователя стоит проверка крутости на пароль - у него там критерии, короче много символов цифру спец символ и тогда точно пароль примет и с ним можно войти за другого пользователя.
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('habits')
        else:
            return render(request, 'registration/login.html', {'error': 'Неверные данные'})
    return render(request, 'registration/login.html')

def home(request):
    return redirect('habits')
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/accounts/login')
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
