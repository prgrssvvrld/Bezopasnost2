from django import forms
from .models import Habit, CustomUser  # Убедитесь, что вы импортируете вашу кастомную модель
from django.contrib.auth.forms import UserCreationForm

class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['category', 'name', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'placeholder': 'Название привычки'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Описание привычки'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = CustomUser  # Используйте вашу кастомную модель
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser  # Используйте вашу кастомную модель
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }