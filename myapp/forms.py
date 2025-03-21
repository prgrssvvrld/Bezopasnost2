from django import forms
from .models import Habit
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'description']
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']