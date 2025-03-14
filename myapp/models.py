from django.db import models
from django.contrib.auth.models import User

class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Связь с пользователем
    name = models.CharField(max_length=100)  # Название привычки
    description = models.TextField(blank=True)  # Описание привычки
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):
        return self.name
