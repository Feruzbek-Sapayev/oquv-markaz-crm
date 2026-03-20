import uuid
from django.db import models
from students.models import Student
from courses.models import Group


class AttendanceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='sessions', verbose_name='Guruh')
    date = models.DateField(verbose_name='Sana')
    topic = models.CharField(max_length=300, blank=True, verbose_name='Mavzu')
    created_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True,
        related_name='sessions', verbose_name='Qayd etgan'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dars sessiyasi'
        verbose_name_plural = 'Dars sessiyalari'
        unique_together = ['group', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.group} | {self.date}"


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Status(models.TextChoices):
        PRESENT = 'present', 'Keldi'
        ABSENT = 'absent', 'Kelmadi'
        LATE = 'late', 'Kech keldi'
        EXCUSED = 'excused', 'Uzrli'

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records', verbose_name='Sessiya')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances', verbose_name="O'quvchi")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT, verbose_name='Holat')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomat'
        unique_together = ['session', 'student']
        ordering = ['student__last_name']

    def __str__(self):
        return f"{self.student} | {self.session.date} | {self.get_status_display()}"


class DailyGrade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='grades', verbose_name='Sessiya')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='daily_grades', verbose_name="O'quvchi")
    score = models.IntegerField(default=0, verbose_name='Baho')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = 'Kunlik Baho'
        verbose_name_plural = 'Kunlik Baholar'
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student} | {self.session.date} | {self.score}"
