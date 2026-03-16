from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'status', 'hired_at']
    list_filter = ['status', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
