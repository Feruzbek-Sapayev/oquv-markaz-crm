from django.contrib import admin
from .models import Course, Room, Group, Enrollment, Exam, GroupDiscount


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_months', 'monthly_fee', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'is_active']
    list_filter = ['is_active']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active', 'course', 'days']
    search_fields = ['name', 'course__name']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'is_active', 'enrolled_at']
    list_filter = ['is_active', 'group']
    search_fields = ['student__first_name', 'student__last_name', 'student__phone', 'group__name']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'student', 'score', 'max_score', 'date']
    list_filter = ['group', 'date']
    search_fields = ['student__first_name', 'student__last_name', 'title']


@admin.register(GroupDiscount)
class GroupDiscountAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'month', 'year', 'percent']
    list_filter = ['month', 'year']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name']
