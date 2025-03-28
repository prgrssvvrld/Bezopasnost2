from django import forms
from .models import Habit, CustomUser
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
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }