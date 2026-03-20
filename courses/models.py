import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name='Kurs rasmi')
    name = models.CharField(max_length=200, verbose_name='Kurs nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    duration_months = models.PositiveIntegerField(default=6, verbose_name='Davomiyligi (oy)')
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Oylik to\'lov (so\'m)')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Xona nomi')
    capacity = models.PositiveIntegerField(default=0, verbose_name='Sig\'imi (o\'quvchi soni)')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.capacity} o'rin)"


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class DayChoices(models.TextChoices):
        ODD = 'odd', 'Toq kunlar (Du, Ch, Ju)'
        EVEN = 'even', 'Juft kunlar (Se, Pa, Sha)'
        DAILY = 'daily', 'Har kuni'
        WEEKEND = 'weekend', 'Dam olish kunlari'

    class SalaryType(models.TextChoices):
        FIXED = 'fixed', 'Aniq summa'
        PERCENTAGE = 'percentage', 'Foiz'

    name = models.CharField(max_length=100, verbose_name='Guruh nomi')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', verbose_name='Kurs')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='groups', verbose_name="O'qituvchi")
    
    # Salary fields moved from CourseTeacher to Group
    salary_type = models.CharField(max_length=20, choices=SalaryType.choices, default=SalaryType.FIXED, verbose_name='Maosh turi')
    salary_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Oylik maosh')
    salary_percentage = models.IntegerField(default=0, verbose_name='Foiz (%)')

    start_time = models.TimeField(verbose_name='Boshlanish vaqti')
    end_time = models.TimeField(verbose_name='Tugash vaqti')
    days = models.CharField(max_length=20, choices=DayChoices.choices, default=DayChoices.ODD, verbose_name='Dars kunlari')
    start_date = models.DateField(verbose_name='Boshlash sanasi')
    end_date = models.DateField(null=True, blank=True, verbose_name='Tugash sanasi')
    max_students = models.PositiveIntegerField(default=15, verbose_name='Max o\'quvchi soni')
    room_old = models.CharField(max_length=50, blank=True, null=True, verbose_name='Xona (eskicha)')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups', verbose_name='Xona')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.course.name})"

    @property
    def student_count(self):
        return self.enrollments.count()


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        INACTIVE = 'inactive', 'Faol emas'
        GRADUATED = 'graduated', 'Bitirgan'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='enrollments', verbose_name="O'quvchi")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Guruh')
    enrolled_at = models.DateField(default=timezone.now, verbose_name='Qo\'shilgan sana')
    left_at = models.DateField(null=True, blank=True, verbose_name='Ketgan sana')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Holat')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    discount_percent = models.PositiveIntegerField(default=0, verbose_name='Chegirma (%)')
    notes = models.TextField(blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = "Ro'yxat"
        verbose_name_plural = "Ro'yxatlar"
        unique_together = ['student', 'group']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student} → {self.group}"

    def save(self, *args, **kwargs):
        self.is_active = (self.status == self.Status.ACTIVE)
        if not self.is_active and not self.left_at:
            self.left_at = timezone.now().date()
        elif self.is_active:
            self.left_at = None
        super().save(*args, **kwargs)

    def get_discounted_fee_for_month(self, month, year):
        if self.status != self.Status.ACTIVE:
            return 0
        from decimal import Decimal
        original = Decimal(str(self.group.course.monthly_fee))
        discounts = self.discounts.filter(month=month, year=year)
        
        total_percent = 0
        total_fixed = Decimal('0')
        
        if discounts.exists():
            for d in discounts:
                if d.discount_type == GroupDiscount.DiscountType.PERCENTAGE:
                    total_percent += d.percent
                else:
                    total_fixed += d.amount
        else:
            total_percent = self.discount_percent
            
        fee_after_percent = original * (Decimal('100') - Decimal(str(total_percent))) / Decimal('100')
        expected_amount = max(Decimal('0'), fee_after_percent - total_fixed)
        
        return expected_amount

    @property
    def discounted_fee(self):
        # Default to current month/year for the property
        from django.utils import timezone
        today = timezone.now().date()
        return self.get_discounted_fee_for_month(today.month, today.year)

    @property
    def get_total_payments(self):
        from payments.models import Payment
        from django.db.models import Sum
        return Payment.objects.filter(
            student=self.student, 
            group=self.group
        ).aggregate(total=Sum('amount'))['total'] or 0

    @property
    def get_balance(self):
        from decimal import Decimal
        return Decimal(str(self.get_total_payments)) - self.get_overdue_expected_fees

    @property
    def get_overdue_expected_fees(self):
        from django.utils import timezone
        from decimal import Decimal
        import datetime
        import calendar

        today = timezone.now().date()
        total_expected = Decimal('0')
        monthly_fee = self.group.course.monthly_fee
        
        # Prefetch discounts
        discounts = list(self.discounts.all())
        
        current_date = datetime.date(self.enrolled_at.year, self.enrolled_at.month, 1)
        
        end_date = today
        if not self.is_active and self.left_at:
            end_date = self.left_at
            
        while current_date <= datetime.date(end_date.year, end_date.month, 1):
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            due_day = min(self.group.start_date.day, last_day)
            due_date = datetime.date(current_date.year, current_date.month, due_day)
            
            if end_date < due_date:
                break
            
            # Aggregate discounts for this specific month
            percent = self.discount_percent
            month_fixed_amount = Decimal('0')
            has_month_discounts = False
            
            for d in discounts:
                if d.month == current_date.month and d.year == current_date.year:
                    if not has_month_discounts:
                        percent = 0 # Reset default if specific month discounts exist
                        has_month_discounts = True
                    
                    if d.discount_type == GroupDiscount.DiscountType.PERCENTAGE:
                        percent += d.percent
                    else:
                        month_fixed_amount += d.amount
            
            fee_after_percent = monthly_fee * (Decimal('100') - Decimal(str(percent))) / Decimal('100')
            month_expected = max(Decimal('0'), fee_after_percent - month_fixed_amount)
            total_expected += month_expected
            
            if current_date.month == 12:
                current_date = datetime.date(current_date.year + 1, 1, 1)
            else:
                current_date = datetime.date(current_date.year, current_date.month + 1, 1)
                
        return total_expected

    def get_total_debt(self):
        from decimal import Decimal
        return max(Decimal('0'), -self.get_balance)

    @property
    def get_current_discount(self):
        if self.status != self.Status.ACTIVE:
            return 0
        from django.utils import timezone
        today = timezone.now().date()
        discount = self.discounts.filter(month=today.month, year=today.year).first()
        return discount.percent if discount else 0

    @property
    def current_month_payment_details(self):
        from django.utils import timezone
        import datetime
        from decimal import Decimal
        from payments.models import Payment
        
        today = timezone.now().date()
        if self.status != self.Status.ACTIVE:
            return {'amount': 0, 'percent': 0, 'is_paid': False, 'is_active': False}
            
        monthly_fee = Decimal(str(self.group.course.monthly_fee))
        
        # Check if student is even enrolled yet for this month
        if self.enrolled_at > today:
            return {'amount': 0, 'percent': 0, 'is_paid': True, 'is_active': True}
            
        discounts = self.discounts.filter(month=today.month, year=today.year)
        percent = 0
        total_fixed = Decimal('0')
        has_month_discounts = False
        
        if discounts.exists():
            has_month_discounts = True
            for d in discounts:
                if d.discount_type == GroupDiscount.DiscountType.PERCENTAGE:
                    percent += d.percent
                else:
                    total_fixed += d.amount
        else:
            percent = self.discount_percent
            
        fee_after_percent = monthly_fee * (Decimal('100') - Decimal(str(percent))) / Decimal('100')
        expected_amount = max(Decimal('0'), fee_after_percent - total_fixed)
        
        # Current month's due date based on group's start date
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        this_month_due_date = datetime.date(today.year, today.month, min(self.group.start_date.day, last_day))
        
        # Check if current balance is enough to cover this month's fee OR it's not yet due date
        balance = self.get_balance
        is_paid = (balance >= expected_amount) or (today < this_month_due_date)
        
        return {
            'amount': int(expected_amount),
            'percent': percent,
            'discount_amount': int(total_fixed),
            'has_fixed': total_fixed > 0,
            'is_paid': is_paid,
            'is_active': True
        }

    @property
    def next_payment_date(self):
        from django.utils import timezone
        import datetime
        import calendar
        from decimal import Decimal

        if self.status != self.Status.ACTIVE:
            return None

        today = timezone.now().date()
        total_paid = Decimal(str(self.get_total_payments))
        monthly_fee = Decimal(str(self.group.course.monthly_fee))
        discounts = list(self.discounts.all())

        current_date = datetime.date(self.enrolled_at.year, self.enrolled_at.month, 1)
        total_expected = Decimal('0')

        # Limit iterations to avoid infinite loop (e.g., 36 months)
        for _ in range(36):
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            due_day = min(self.group.start_date.day, last_day)
            due_date = datetime.date(current_date.year, current_date.month, due_day)

            # Aggregate discounts for this month
            percent = self.discount_percent
            month_fixed_amount = Decimal('0')
            has_month_discounts = False
            
            for d in discounts:
                if d.month == current_date.month and d.year == current_date.year:
                    if not has_month_discounts:
                        percent = 0
                        has_month_discounts = True
                    
                    if d.discount_type == GroupDiscount.DiscountType.PERCENTAGE:
                        percent += d.percent
                    else:
                        month_fixed_amount += d.amount
            
            fee_after_percent = monthly_fee * (Decimal('100') - Decimal(str(percent))) / Decimal('100')
            month_expected = max(Decimal('0'), fee_after_percent - month_fixed_amount)
            total_expected += month_expected

            if total_expected > total_paid:
                return due_date
            
            # Advance month
            if current_date.month == 12:
                current_date = datetime.date(current_date.year+1, 1, 1)
            else:
                current_date = datetime.date(current_date.year, current_date.month+1, 1)
        
        return None


class GroupDiscount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Foiz (%)'
        FIXED = 'fixed', 'Aniq summa (so\'m)'

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='discounts', verbose_name="Ro'yxat")
    month = models.PositiveIntegerField(verbose_name='Tanlangan oy (1-12)')
    year = models.PositiveIntegerField(verbose_name='Tanlangan yil')
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE, verbose_name='Chegirma turi')
    percent = models.PositiveIntegerField(default=0, verbose_name='Chegirma (%)')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Chegirma summasi')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        try:
            if self.enrollment and self.enrollment.status != Enrollment.Status.ACTIVE:
                raise ValidationError("Faqat faol o'quvchilarga chegirma berish mumkin!")
        except (Enrollment.DoesNotExist, AttributeError):
            pass

    def save(self, *args, **kwargs):
        # We don't call full_clean here because ModelForms do it automatically.
        # If created via ORM, developers should handle validation or call it manually.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Chegirma'
        verbose_name_plural = 'Chegirmalar'
        ordering = ['-created_at']

    def __str__(self):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            label = f"{self.percent}%"
        else:
            label = f"{self.amount} so'm"
        return f"{label} Chegirma: {self.enrollment.student} ({self.month}/{self.year})"

class Exam(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exams', verbose_name="O'quvchi")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='exams', verbose_name='Guruh')
    title = models.CharField(max_length=200, verbose_name='Imtihon nomi (masalan: Unit 1 Test)')
    score = models.IntegerField(verbose_name='Ball')
    max_score = models.IntegerField(default=100, verbose_name='Maksimal ball')
    date = models.DateField(verbose_name='Sana')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imtihon'
        verbose_name_plural = 'Imtihonlar'
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.title} ({self.score}/{self.max_score})"
