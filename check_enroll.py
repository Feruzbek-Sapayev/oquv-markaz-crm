import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from courses.models import Enrollment

umida_enrolls = Enrollment.objects.filter(student__last_name='Mahmudova', student__first_name='Umida')
for e in umida_enrolls:
    print(f"Student: {e.student}, Group: {e.group}, Status: '{e.status}', is_active: {e.is_active}")
