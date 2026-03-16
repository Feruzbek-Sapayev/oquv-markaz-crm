from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'status', 'registered_at']
    list_filter = ['status', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'parent_phone']
