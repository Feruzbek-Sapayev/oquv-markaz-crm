from django.contrib import admin
from .models import AdminProfile

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'birth_date', 'phone')
    search_fields = ('user__username', 'first_name', 'last_name', 'phone')
