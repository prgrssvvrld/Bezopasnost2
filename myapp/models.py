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
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

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
    CATEGORY_CHOICES = [
        ('health', 'Здоровье'),
        ('sport', 'Спорт'),
        ('study', 'Учеба'),
        ('work', 'Работа'),
        ('other', 'Другое'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='health')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name
