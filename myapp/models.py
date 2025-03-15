from django.db import models
from django.conf import settings  # Import settings for AUTH_USER_MODEL
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission  # Import Group and Permission
from django.utils.translation import gettext_lazy as _  # For translating verbose_name


class CustomUser(AbstractUser):
    """
    Custom user model.
    """
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_set",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_set",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):  # Corrected to __str__
        return self.username


class Habit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Исправлена связь с пользователем
    name = models.CharField(max_length=100)  # Название привычки
    description = models.TextField(blank=True)  # Описание привычки
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания

    def __str__(self):  # Corrected to __str__
        return self.name
