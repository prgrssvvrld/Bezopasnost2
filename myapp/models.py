from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings  # Import settings for AUTH_USER_MODEL
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission  # Import Group and Permission
from django.utils.translation import gettext_lazy as _  # For translating verbose_name
from datetime import timedelta


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

    verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_code_created_at = models.DateTimeField(null=True, blank=True)


class Habit(models.Model):
    CATEGORY_CHOICES = [
        ('health', 'Здоровье'),
        ('productivity', 'Продуктивность'),
        ('learning', 'Обучение'),
        ('relationships', 'Отношения'),
        ('finance', 'Финансы'),
    ]

    COLOR_CHOICES = [
        ('bg-red-100 text-red-800', 'Красный'),
        ('bg-blue-100 text-blue-800', 'Синий'),
        ('bg-green-100 text-green-800', 'Зеленый'),
        ('bg-yellow-100 text-yellow-800', 'Желтый'),
        ('bg-purple-100 text-purple-800', 'Фиолетовый'),
        ('bg-pink-100 text-pink-800', 'Розовый'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # <- это разрешает хранить NULL в БД
        blank=True  # <- это позволяет оставить поле пустым в админке
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    days_goal = models.PositiveIntegerField(default=30)
    color_class = models.CharField(max_length=50, choices=COLOR_CHOICES, default='bg-gray-100 text-gray-800')
    reminder = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_current_streak(self):
        """Возвращает текущую серию последовательных выполненных дней (исправленная версия)"""
        today = timezone.now().date()
        completions = self.completions.filter(
            date__lte=today
        ).order_by('-date')

        streak = 0
        prev_date = None

        for completion in completions:
            if prev_date is None:
                # Первая запись - проверяем что это сегодня или вчера
                if completion.date == today:
                    streak = 1
                    prev_date = completion.date
                elif (today - completion.date).days == 1:
                    streak = 1
                    prev_date = completion.date
                else:
                    break
            else:
                if (prev_date - completion.date).days == 1:
                    streak += 1
                    prev_date = completion.date
                else:
                    break

        return streak


    def get_longest_streak(self):
        """Возвращает самую длинную серию последовательных выполненных дней"""
        completions = list(self.completions.order_by('date'))
        if not completions:
            return 0

        longest = current = 1

        for i in range(1, len(completions)):
            if (completions[i].date - completions[i-1].date).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest

    def get_completion_rate(self):
        total_completions = self.completions.filter(completed=True).count()
        return min(100, int((total_completions / self.days_goal) * 100))

    def is_completed_today(self):
        """Проверяет, выполнена ли привычка сегодня"""
        today = timezone.now().date()
        return self.completions.filter(date=today).exists()

    def is_completed_on(self, date):
        return self.completions.filter(date=date, completed=True).exists()

    def mark_as_completed(self):
        """Отмечает привычку как выполненную на сегодня"""
        today = timezone.now().date()

        if self.is_completed_today():
            raise ValidationError("Эта привычка уже выполнена сегодня")

        HabitCompletion.objects.create(habit=self, date=today)

    def is_completed_on_current_date(self, date):
        """Проверяет, выполнена ли привычка в указанную дату"""
        return self.completions.filter(date=date).exists()

    def get_completion_days(self):
        scheduled_days = list(self.schedule.values_list('day_of_week', flat=True))
        if not scheduled_days:
            return []

        start_date = self.created_at.date() if self.created_at else timezone.now().date()
        completion_days = []
        current_date = start_date
        max_days_to_check = 365

        while len(completion_days) < self.days_goal and (current_date - start_date).days < max_days_to_check:
            if current_date.weekday() in scheduled_days:
                completion_days.append(current_date)
            current_date += timedelta(days=1)

        completed_dates = set(
            self.completions.filter(
                date__in=completion_days,
                completed=True
            ).values_list('date', flat=True)
        )

        return [{
            'date': date,
            'completed': date in completed_dates
        } for date in completion_days]


class HabitSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    habit = models.ForeignKey(Habit, related_name='schedule', on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)

    class Meta:
        unique_together = ('habit', 'day_of_week')

    def __str__(self):
        return f"{self.habit.name} - {self.get_day_of_week_display()}"

# models.py
class HabitCompletion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    date = models.DateField()
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('habit', 'date')

    def __str__(self):
        return f"{self.habit.name} - {self.date} ({'Completed' if self.completed else 'Not completed'})"

