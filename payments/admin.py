from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'month', 'year', 'amount', 'status', 'method', 'paid_at']
    list_filter = ['status', 'method', 'year', 'month']
    search_fields = ['student__first_name', 'student__last_name', 'student__phone', 'group__name']
