import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        TEACHER = 'teacher', "O'qituvchi"
        STUDENT = 'student', "O'quvchi"
        ACCOUNTANT = 'accountant', 'Buxgalter'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN

    @property
    def is_admin_role(self):
        return self.role in [self.Role.SUPERADMIN, self.Role.ADMIN]

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        
        # Check profiles based on role
        if hasattr(self, 'admin_profile') and self.admin_profile.photo:
            return self.admin_profile.photo.url
        if hasattr(self, 'teacher_profile') and self.teacher_profile.photo:
            return self.teacher_profile.photo.url
        if hasattr(self, 'student_profile') and self.student_profile.photo:
            return self.student_profile.photo.url
        
        return None
