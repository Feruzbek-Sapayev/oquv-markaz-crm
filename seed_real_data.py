import os
import django
import random
from datetime import date, time, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Group, Enrollment
from payments.models import Payment
from attendance.models import AttendanceSession, Attendance

User = get_user_model()

# Uzbek names and surnames
first_names_m = ["Ali", "Vali", "Hasan", "Husan", "Javohir", "Sardor", "Nodir", "Temur", "Aziz", "Rustam", "Umid", "Jamshid", "Shavkat", "Oybek", "Sanjar", "Jalol", "Botir", "Farhod", "Ilhom", "Qodir"]
first_names_f = ["Malika", "Ziyoda", "Nigora", "Madina", "Sevara", "Shahnoza", "Dilnoza", "Gulnora", "Nargiza", "Umida", "Zarina", "Kamola", "Feruza", "Dildora", "Shahzoda", "Sitora", "Ona", "Gozal", "Nilufar", "Mohira"]
last_names = ["Abdullayev", "Karimov", "Rahimov", "Olimov", "Yusupov", "Toshmatov", "Eshmatov", "Qosimov", "Sharipov", "Usmonov", "Nazarov", "Mamajonov", "Rasulov", "Mahmudov", "Jalilov"]

def get_random_name():
    is_male = random.choice([True, False])
    if is_male:
        return random.choice(first_names_m), random.choice(last_names)
    else:
        return random.choice(first_names_f), random.choice(last_names) + "a"

def get_random_phone():
    return f"+998{random.choice(['90', '91', '93', '94', '97', '99', '88', '95'])}{random.randint(1000000, 9999999)}"

def seed():
    # 1. Teachers
    teachers = []
    print("Creating teachers...")
    for i in range(15):
        fname, lname = get_random_name()
        username = f"teacher_{fname.lower()}_{lname.lower()}_{i}"
        user, created = User.objects.get_or_create(
            username=username, 
            defaults={'first_name': fname, 'last_name': lname, 'role': 'teacher'}
        )
        if created:
            user.set_password('teacher123')
            user.save()
        teacher, _ = Teacher.objects.get_or_create(
            user=user, 
            defaults={'first_name': fname, 'last_name': lname, 'phone': get_random_phone()}
        )
        teachers.append(teacher)
    
    # 2. Courses
    courses_data = [
        ("General English", 450000, 6),
        ("IELTS Preparation", 600000, 4),
        ("CEFR B2", 500000, 5),
        ("Matematika (Milliy Sertifikat)", 500000, 8),
        ("Fizika", 450000, 8),
        ("Ona tili va Adabiyot", 400000, 8),
        ("Python Foundation", 600000, 4),
        ("Frontend (React, Vue)", 700000, 6),
        ("Backend (Django, Node)", 700000, 6),
        ("Arab tili", 450000, 6),
    ]
    courses = []
    print("Creating courses...")
    for name, fee, duration in courses_data:
        c, _ = Course.objects.get_or_create(name=name, defaults={'monthly_fee': fee, 'duration_months': duration})
        courses.append(c)
    
    # 3. Groups
    groups = []
    print("Creating groups...")
    days_choices = ['odd', 'even', 'every']
    for i in range(25):
        course = random.choice(courses)
        teacher = random.choice(teachers)
        start_hour = random.choice([14, 16, 18, 20])
        group, _ = Group.objects.get_or_create(
            name=f"{course.name} - G{i+1}",
            course=course,
            defaults={
                'teacher': teacher,
                'start_time': time(start_hour, 0),
                'end_time': time(start_hour + 2, 0),
                'days': random.choice(days_choices),
                'start_date': date.today() - timedelta(days=random.randint(5, 60)),
                'salary_type': random.choice(['percentage', 'fixed']),
                'salary_percentage': random.choice([40, 50]) if random.random() > 0.5 else 0,
                'salary_monthly': random.choice([1500000, 2000000, 2500000]) if random.random() <= 0.5 else 0,
            }
        )
        
        # Fix missing salary dependencies
        if group.salary_type == 'percentage' and not group.salary_percentage:
            group.salary_percentage = 40
            group.salary_monthly = 0
            group.save()
        elif group.salary_type == 'fixed' and not group.salary_monthly:
            group.salary_monthly = 2000000
            group.salary_percentage = 0
            group.save()
            
        groups.append(group)
    
    # 4. Students & Enrollments
    students = []
    print("Creating 150 students...")
    for i in range(150):
        fname, lname = get_random_name()
        username = f"student_{fname.lower()}_{lname.lower()}_{i}"
        user, created = User.objects.get_or_create(
            username=username, 
            defaults={'first_name': fname, 'last_name': lname, 'role': 'student'}
        )
        if created:
            user.set_password('student123')
            user.save()
        student, _ = Student.objects.get_or_create(
            user=user, 
            defaults={'first_name': fname, 'last_name': lname, 'phone': get_random_phone()}
        )
        students.append(student)
        
        # Enroll in 1 to 2 random groups
        num_enrollments = random.choices([1, 2], weights=[80, 20])[0]
        enrollment_groups = random.sample(groups, num_enrollments)
        for g in enrollment_groups:
            Enrollment.objects.get_or_create(student=student, group=g)
            
    # 5. Attendance & Payments
    print("Creating attendance and payments...")
    for group in groups:
        enrollments = Enrollment.objects.filter(group=group)
        if not enrollments.exists():
            continue
            
        # Attendance for last 5 lessons
        for i in range(5):
            d = date.today() - timedelta(days=i*2 + 1)
            session, _ = AttendanceSession.objects.get_or_create(
                group=group, date=d, defaults={'topic': f'Lesson {5-i}'}
            )
            for e in enrollments:
                status = random.choices(['present', 'absent', 'late'], weights=[85, 10, 5])[0]
                Attendance.objects.get_or_create(
                    session=session, student=e.student, defaults={'status': status}
                )
                
        # Payments for current month
        for e in enrollments:
            is_paid = random.random() > 0.3
            amount = group.course.monthly_fee if is_paid else (group.course.monthly_fee / 2 if random.random() > 0.5 else 0)
            if amount > 0:
                Payment.objects.get_or_create(
                    student=e.student,
                    group=group,
                    month=date.today().month,
                    year=date.today().year,
                    defaults={
                        'amount': amount,
                        'expected_amount': group.course.monthly_fee,
                        'method': random.choice(['cash', 'card']),
                        'paid_at': date.today() - timedelta(days=random.randint(0, 10)),
                        'status': 'paid' if amount == group.course.monthly_fee else 'partial'
                    }
                )
    print("Seeding Complete!")

if __name__ == "__main__":
    seed()
