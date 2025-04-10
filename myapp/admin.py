from django.contrib import admin
from .models import Category, Habit

class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_template', 'user')
    list_filter = ('category', 'is_template')
    search_fields = ('name',)

admin.site.register(Category)
admin.site.register(Habit)
# Register your models here.
