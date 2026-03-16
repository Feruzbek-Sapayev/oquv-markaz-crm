import uuid
from django.db import models


from django.conf import settings

class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='teacher_profile', null=True, blank=True,
        verbose_name='Foydalanuvchi'
    )
    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        INACTIVE = 'inactive', 'Faol emas'

    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    email = models.EmailField(blank=True, verbose_name='Email')
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE, verbose_name='Jins')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tug\'ilgan sana')
    address = models.TextField(blank=True, verbose_name='Manzil')
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True, verbose_name='Rasm')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Holat')
    hired_at = models.DateField(null=True, blank=True, verbose_name='Ishga kirgan sana')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"
        ordering = ['-created_at', 'last_name']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def get_stats(self):
        """Calculates performance statistics for the teacher."""
        from courses.models import Group, Enrollment, Exam
        from attendance.models import Attendance
        from django.db.models import Avg

        # Get groups taught by this teacher
        teacher_groups = self.groups.all()
        
        # Current active students
        active_enrollments = Enrollment.objects.filter(group__in=teacher_groups, is_active=True).distinct()
        total_active_students = active_enrollments.values('student').distinct().count()

        # Average Attendance
        att_rate = 0
        sessions_total = Attendance.objects.filter(session__group__in=teacher_groups).count()
        if sessions_total > 0:
            present = Attendance.objects.filter(session__group__in=teacher_groups, status__in=['present', 'late']).count()
            att_rate = (present / sessions_total) * 100

        # Average Exam Score
        avg_score = Exam.objects.filter(group__in=teacher_groups).aggregate(avg=Avg('score'))['avg'] or 0

        # Retention Rate
        total_ever = Enrollment.objects.filter(group__in=teacher_groups).values('student').distinct().count()
        retention_rate = (total_active_students / total_ever * 100) if total_ever > 0 else 0

        return {
            'active_students': total_active_students,
            'attendance_rate': round(att_rate, 1),
            'average_score': round(avg_score, 1),
            'retention_rate': round(retention_rate, 1),
        }
