from django.contrib import admin
from .models import AttendanceSession, Attendance


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['group', 'date', 'created_by', 'created_at']
    list_filter = ['date', 'group']
    search_fields = ['group__name', 'group__course__name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status']
    list_filter = ['status', 'session__group']
    search_fields = ['student__first_name', 'student__last_name', 'student__phone', 'session__group__name']
