from django import forms
from .models import Habit, CustomUser, Weekday, Category  # Убедитесь, что вы импортируете все нужные модели
from django.contrib.auth.forms import UserCreationForm

class HabitForm(forms.ModelForm):
    # Добавление поля для выбора дней недели
    weekdays = forms.ModelMultipleChoiceField(
        queryset=Weekday.objects.all(),  # Получаем все дни недели
        widget=forms.CheckboxSelectMultiple,  # Для отображения множества флажков
        required=False,
        label="Выберите дни недели"
    )

    class Meta:
        model = Habit
        fields = ['name', 'description', 'category', 'weekdays']  # Включаем поле weekdays
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),  # Кастомизация поля Select для категорий
            'name': forms.TextInput(attrs={'placeholder': 'Название привычки'}),  # Кастомизация для name
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Описание привычки'}),  # Кастомизация для description
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
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),  # Кастомизация для profile_picture
            'bio': forms.Textarea(attrs={'rows': 4}),  # Кастомизация для bio
        }
