import uuid
from django.db import models
from students.models import Student
from courses.models import Group


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        PAID = 'paid', "To'langan"
        UNPAID = 'unpaid', "To'lanmagan"
        PARTIAL = 'partial', 'Qisman to\'langan'

    class Method(models.TextChoices):
        CASH = 'cash', 'Naqd'
        CARD = 'card', 'Karta'
        TRANSFER = 'transfer', "Bank o'tkazma"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments', verbose_name="O'quvchi")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='payments', verbose_name='Guruh')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="To'lov miqdori (so'm)")
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Kutilgan miqdor")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID, verbose_name='Holat')
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH, verbose_name="To'lov usuli")
    month = models.PositiveIntegerField(verbose_name='Oy (raqam)', help_text='1-12')
    year = models.PositiveIntegerField(verbose_name='Yil')
    paid_at = models.DateField(null=True, blank=True, verbose_name="To'langan sana")
    due_date = models.DateField(null=True, blank=True, verbose_name='Muddati')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recorded_payments', verbose_name='Qo\'shgan hodim'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-year', '-month', '-created_at']

    def __str__(self):
        return f"{self.student} | {self.group} | {self.month}/{self.year} | {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.amount >= self.expected_amount:
            self.status = self.Status.PAID
        elif self.amount > 0:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.UNPAID
        super().save(*args, **kwargs)

    @property
    def remaining(self):
        return max(0, self.expected_amount - self.amount)
