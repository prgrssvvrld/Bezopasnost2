from django import forms
from .models import Habit, CustomUser, Weekday, Category  # Убедитесь, что вы импортируете все нужные модели
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"

        self.fields['password1'].help_text = (
            "Пароль должен содержать не менее 8 символов, "
            "включать цифры, буквы в разных регистрах и специальные символы."
        )
        self.fields['password2'].help_text = "Повторите пароль для подтверждения."

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        return password2

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser  # Используйте вашу кастомную модель
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),  # Кастомизация для profile_picture
            'bio': forms.Textarea(attrs={'rows': 4}),  # Кастомизация для bio
        }
