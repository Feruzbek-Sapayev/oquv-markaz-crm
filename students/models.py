import uuid
from django.db import models


from django.conf import settings

class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='student_profile', null=True, blank=True,
        verbose_name='Foydalanuvchi'
    )
    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        INACTIVE = 'inactive', 'Faol emas'
        GRADUATED = 'graduated', 'Bitirgan'

    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Ota-ona telefoni')
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE, verbose_name='Jins')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tug\'ilgan sana')
    address = models.TextField(blank=True, verbose_name='Manzil')
    photo = models.ImageField(upload_to='students/', blank=True, null=True, verbose_name='Rasm')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Holat')
    registered_at = models.DateField(auto_now_add=True, verbose_name='Ro\'yxatdan o\'tgan sana')
    telegram_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Telegram ID')
    telegram_notifications = models.BooleanField(default=True, verbose_name='Telegram xabarnomalar')
    notes = models.TextField(blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering = ['-registered_at', 'last_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @property
    def active_enrollments(self):
        return self.enrollments.filter(is_active=True).select_related('group__course', 'group__teacher')

    @property
    def total_debt(self):
        from payments.models import Payment
        from django.db.models import Sum
        paid = Payment.objects.filter(student=self, status__in=['paid', 'partial']) \
                              .aggregate(total=Sum('amount'))['total'] or 0
        # calculate expected = sum of monthly fees
        expected = sum(
            e.group.course.monthly_fee
            for e in self.enrollments.filter(is_active=True).select_related('group__course')
        )
        return max(0, expected - paid)

    @property
    def lead_status(self):
        """
        Returns {icon, color, label} based on attendance and payments.
        """
        from datetime import date, timedelta
        from attendance.models import Attendance
        from payments.models import Payment

        # 1. Attendance Check (Last 10 sessions)
        last_attendances = list(Attendance.objects.filter(student=self).order_by('-session__date')[:10])
        attendance_count = len(last_attendances)
        if attendance_count > 0:
            present_count = len([a for a in last_attendances if a.status in ['present', 'late']])
            att_rate = (present_count / attendance_count) * 100
        else:
            att_rate = 100 # New students start neutral

        # 2. Debt Check
        has_debt = Payment.objects.filter(student=self, status__in=['unpaid', 'partial']).exists()

        if att_rate >= 90 and not has_debt:
            return {'icon': '⭐', 'color': '#fbbf24', 'label': 'Top', 'desc': 'Ideal o\'quvchi'}
        elif att_rate >= 70:
            return {'icon': '🔥', 'color': '#f87171', 'label': 'Faol', 'desc': 'Yaxshi qatnashmoqda'}
        elif att_rate < 50 or has_debt:
            return {'icon': '❄️', 'color': '#60a5fa', 'label': 'Sust', 'desc': 'E\'tibor kerak'}
        
        return {'icon': '⚡', 'color': '#a78bfa', 'label': 'Oddiy', 'desc': 'Barqaror'}
