import os
import django
import random
from datetime import date, timedelta, time
from decimal import Decimal

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Group, Enrollment
from payments.models import Payment
from attendance.models import AttendanceSession, Attendance
from accounts.models import CustomUser

def clear_data():
    print("Clearing existing data...")
    Attendance.objects.all().delete()
    AttendanceSession.objects.all().delete()
    Payment.objects.all().delete()
    Enrollment.objects.all().delete()
    Group.objects.all().delete()
    Course.objects.all().delete()
    # Don't delete staff users to avoid login issues, but delete profiles
    Student.objects.all().delete()
    Teacher.objects.all().delete()
    
    # Delete users that are NOT staff/superuser
    CustomUser.objects.filter(is_staff=False, is_superuser=False).delete()

def seed_data():
    uz_surnames = ['Karimov', 'Yusupov', 'Abdullayev', 'Ismoilov', 'Nabiyev', 'Rustamov', 'Sharipov', 'Ergashev', 'G\'ofurov', 'Soliyev', 'Toshpo\'latov', 'Mirzayev']
    uz_male_names = ['Alisher', 'Sardor', 'Javohir', 'Bobur', 'Nodir', 'Aziz', 'Bekzod', 'Temur', 'Dilshod', 'Otabek', 'Jasur', 'Farhod']
    uz_female_names = ['Gulnora', 'Madina', 'Sevara', 'Nigora', 'Laylo', 'Malika', 'Zulfiya', 'Rayhon', 'Dilnoza', 'Shahnoza', 'Kamola', 'Durdona']
    
    print("Creating teachers...")
    teachers = []
    for i in range(5):
        is_male = random.choice([True, False])
        first_name = random.choice(uz_male_names if is_male else uz_female_names)
        last_name = random.choice(uz_surnames)
        t = Teacher.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=f"+99890{random.randint(1000000, 9999999)}",
            gender='male' if is_male else 'female',
            status='active',
            hired_at=date.today() - timedelta(days=random.randint(200, 500)),
            salary_monthly=Decimal(random.randint(3000000, 7000000))
        )
        teachers.append(t)

    print("Creating courses...")
    courses_data = [
        ("General English (Beginner)", 6, 450000),
        ("IELTS Preparation", 4, 650000),
        ("Matematika (DTM)", 10, 400000),
        ("Python Dasturlash", 6, 800000),
    ]
    courses = []
    for name, dur, fee in courses_data:
        c = Course.objects.create(name=name, duration_months=dur, monthly_fee=fee)
        courses.append(c)

    print("Creating groups...")
    groups = []
    group_suffixes = ['Morning', 'Afternoon', 'Evening', 'Group A', 'Group B', 'Fast Track']
    for i, course in enumerate(courses):
        for j in range(2):
            g = Group.objects.create(
                name=f"{course.name[:3].upper()}-{random.choice(group_suffixes)}",
                course=course,
                teacher=random.choice(teachers),
                start_time=time(hour=9 + (j*3)),
                end_time=time(hour=11 + (j*3)),
                days=random.choice(['odd', 'even', 'daily']),
                start_date=date.today() - timedelta(days=random.randint(10, 60)),
                max_students=15,
                room=f"Room {random.randint(1, 10)}",
                is_active=True
            )
            groups.append(g)

    print("Creating students...")
    students = []
    for i in range(40):
        is_male = random.choice([True, False])
        first_name = random.choice(uz_male_names if is_male else uz_female_names)
        last_name = random.choice(uz_surnames)
        s = Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=f"+99891{random.randint(1000000, 9999999)}",
            gender='male' if is_male else 'female',
            birth_date=date(random.randint(1995, 2010), random.randint(1, 12), random.randint(1, 28)),
            status='active'
        )
        students.append(s)

    print("Enrolling students...")
    for student in students:
        # Enroll in 1-2 random groups
        num_enrollments = random.randint(1, 2)
        target_groups = random.sample(groups, num_enrollments)
        for group in target_groups:
            Enrollment.objects.get_or_create(student=student, group=group, is_active=True)

    print("Seeding attendance and payments...")
    today = date.today()
    last_month = (today.replace(day=1) - timedelta(days=1))
    
    for group in groups:
        enrollments = group.enrollments.filter(is_active=True)
        # 4 sessions per month approx
        for d in range(1, 28, 7):
            session_date = last_month.replace(day=d)
            session, _ = AttendanceSession.objects.get_or_create(group=group, date=session_date)
            for e in enrollments:
                status = random.choices(['present', 'absent', 'late'], weights=[80, 15, 5])[0]
                Attendance.objects.get_or_create(session=session, student=e.student, status=status)
        
        # Payments for last month
        for e in enrollments:
            fee = e.discounted_fee
            pay_status = random.choices(['paid', 'partial', 'unpaid'], weights=[70, 20, 10])[0]
            if pay_status == 'paid':
                amount = fee
            elif pay_status == 'partial':
                amount = fee / 2
            else:
                amount = 0
            
            Payment.objects.create(
                student=e.student,
                group=group,
                amount=amount,
                expected_amount=fee,
                status=pay_status,
                month=last_month.month,
                year=last_month.year,
                paid_at=last_month if amount > 0 else None
            )

if __name__ == "__main__":
    clear_data()
    seed_data()
    print("Database reset and seeded successfully!")
