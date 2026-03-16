import uuid
from django.db import models
from django.conf import settings

class AdminProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='admin_profile',
        verbose_name='Foydalanuvchi'
    )
    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tug\'ilgan sana')
    photo = models.ImageField(upload_to='admins/', blank=True, null=True, verbose_name='Rasm')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Profili"
        verbose_name_plural = "Admin Profillari"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()
