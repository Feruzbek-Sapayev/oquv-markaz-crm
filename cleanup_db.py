import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Group, Enrollment, Exam
from payments.models import Payment
from attendance.models import AttendanceSession, Attendance

User = get_user_model()

def cleanup():
    print("Starting database cleanup...")
    
    # 1. Identify 10 students to keep
    students_to_keep = Student.objects.all().order_by('id')[:10]
    keep_student_pks = list(students_to_keep.values_list('pk', flat=True))
    keep_user_pks = list(students_to_keep.values_list('user_id', flat=True))
    
    # 2. Identify Superusers to keep
    superusers = User.objects.filter(is_superuser=True)
    for su in superusers:
        keep_user_pks.append(su.pk)
        
    print(f"Keeping {len(keep_student_pks)} students and {len(set(keep_user_pks))} users.")

    # 3. Clear data from other tables
    # Deleting Courses will cascade to Groups, Enrollments, AttendanceSessions, Exams (usually)
    print("Deleting attendance...")
    Attendance.objects.all().delete()
    AttendanceSession.objects.all().delete()
    
    print("Deleting payments...")
    Payment.objects.all().delete()
    
    print("Deleting enrollments and exams...")
    Enrollment.objects.all().delete()
    Exam.objects.all().delete()
    
    print("Deleting groups and courses...")
    Group.objects.all().delete()
    Course.objects.all().delete()
    
    print("Deleting teachers...")
    Teacher.objects.all().delete()
    
    # 4. Delete students not in the keep list
    print("Deleting students not on the keep list...")
    Student.objects.exclude(pk__in=keep_student_pks).delete()
    
    # 5. Delete users not in the keep list
    print("Deleting users not on the keep list...")
    User.objects.exclude(pk__in=keep_user_pks).delete()
    
    print("Cleanup Complete! Remaining Students:", Student.objects.count())
    print("Remaining Users:", User.objects.count())

if __name__ == "__main__":
    cleanup()
