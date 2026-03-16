import os
import django
import uuid
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Group, Enrollment
from payments.models import Payment
from attendance.models import AttendanceSession, Attendance

User = get_user_model()

def seed():
    # 1. Create Superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='superadmin')
        print("Superuser created: admin / admin123")

    # 2. Create Courses
    c1, _ = Course.objects.get_or_create(
        name="Ingliz tili (General English)",
        defaults={'monthly_fee': 450000, 'duration_months': 6}
    )
    c2, _ = Course.objects.get_or_create(
        name="Matematika (Pre-Calculus)",
        defaults={'monthly_fee': 400000, 'duration_months': 8}
    )
    c3, _ = Course.objects.get_or_create(
        name="Foundation IT (Python)",
        defaults={'monthly_fee': 550000, 'duration_months': 4}
    )
    print("Courses created.")

    # 3. Create Teachers
    t1_user, _ = User.objects.get_or_create(
        username='teacher_john',
        defaults={'first_name': 'John', 'last_name': 'Doe', 'role': 'teacher'}
    )
    t1_user.set_password('teacher123')
    t1_user.save()
    t1, _ = Teacher.objects.get_or_create(
        user=t1_user,
        defaults={'first_name': 'John', 'last_name': 'Doe', 'phone': '+998901234567'}
    )

    t2_user, _ = User.objects.get_or_create(
        username='teacher_jane',
        defaults={'first_name': 'Jane', 'last_name': 'Smith', 'role': 'teacher'}
    )
    t2_user.set_password('teacher123')
    t2_user.save()
    t2, _ = Teacher.objects.get_or_create(
        user=t2_user,
        defaults={'first_name': 'Jane', 'last_name': 'Smith', 'phone': '+998907654321'}
    )
    print("Teachers created.")

    # 4. Create Groups
    g1, _ = Group.objects.get_or_create(
        name="English Group A1",
        course=c1,
        defaults={
            'teacher': t1,
            'start_time': time(14, 0),
            'end_time': time(16, 0),
            'days': 'odd',
            'start_date': date.today() - timedelta(days=30),
            'salary_type': 'percentage',
            'salary_percentage': 40
        }
    )

    g2, _ = Group.objects.get_or_create(
        name="Python Beginners",
        course=c3,
        defaults={
            'teacher': t2,
            'start_time': time(18, 0),
            'end_time': time(20, 0),
            'days': 'even',
            'start_date': date.today() - timedelta(days=15),
            'salary_type': 'fixed',
            'salary_monthly': 2000000
        }
    )
    print("Groups created.")

    # 5. Create Students
    students_data = [
        ('Ali', 'Valiyev', '+998991002030'),
        ('Zaynab', 'Karimova', '+998994005060'),
        ('Umar', 'Usmonov', '+998997008090'),
        ('Malika', 'Rustamova', '+998991112233'),
        ('Davron', 'Xoliqov', '+998994445566'),
    ]
    
    for fname, lname, phone in students_data:
        st_user, _ = User.objects.get_or_create(
            username=f"{fname.lower()}_{lname.lower()}",
            defaults={'first_name': fname, 'last_name': lname, 'role': 'student'}
        )
        st_user.set_password('student123')
        st_user.save()
        st, _ = Student.objects.get_or_create(
            user=st_user,
            defaults={'first_name': fname, 'last_name': lname, 'phone': phone}
        )
        
        # Enroll in g1 or g2
        if fname in ['Ali', 'Zaynab', 'Umar']:
            Enrollment.objects.get_or_create(student=st, group=g1)
        else:
            Enrollment.objects.get_or_create(student=st, group=g2)
    print("Students and Enrollments created.")

    # 6. Create Attendance and Payments
    # Add some attendance sessions for Group A1
    for i in range(5):
        d = g1.start_date + timedelta(days=i*2)
        session, _ = AttendanceSession.objects.get_or_create(group=g1, date=d, defaults={'topic': f'Lesson {i+1}'})
        for enrollment in g1.enrollments.all():
            Attendance.objects.get_or_create(session=session, student=enrollment.student, defaults={'status': 'present'})

    # Add a payment for Ali Valiyev
    ali = Student.objects.get(first_name='Ali')
    Payment.objects.get_or_create(
        student=ali,
        group=g1,
        month=date.today().month,
        year=date.today().year,
        defaults={
            'amount': 450000,
            'expected_amount': 450000,
            'method': 'card',
            'paid_at': date.today(),
            'status': 'paid'
        }
    )
    print("Attendance and Payment data created.")

if __name__ == "__main__":
    seed()
