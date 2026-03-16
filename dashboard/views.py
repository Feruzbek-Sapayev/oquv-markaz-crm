from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Group, Enrollment
from payments.models import Payment
from attendance.models import Attendance


@login_required
def home(request):
    User = get_user_model()
    now = timezone.now()
    month = now.month
    year = now.year

    total_students = Student.objects.count()
    total_groups = Group.objects.filter(is_active=True).count()
    total_teachers = User.objects.filter(role='teacher').count()
    
    monthly_income = Payment.objects.filter(
        month=month, year=year, status__in=['paid', 'partial']
    ).aggregate(total=Sum('amount'))['total'] or 0

    debtor_count = Payment.objects.filter(
        month=month, year=year, status__in=['unpaid', 'partial']
    ).values('student').distinct().count()

    total_debt = Payment.objects.filter(
        status__in=['unpaid', 'partial']
    ).aggregate(
        debt=Sum('expected_amount') - Sum('amount')
    )['debt'] or 0

    recent_payments = Payment.objects.select_related(
        'student', 'group__course', 'created_by'
    ).order_by('-created_at')[:8]

    recent_students = Student.objects.order_by('-registered_at')[:6]

    # Monthly income chart data (last 6 months)
    chart_months = []
    chart_income = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        income = Payment.objects.filter(
            month=m, year=y, status__in=['paid', 'partial']
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_months.append(f"{m:02d}/{y}")
        chart_income.append(float(income))

    groups_with_counts = Group.objects.filter(is_active=True).select_related('course').annotate(
        enrolled=Count('enrollments', filter=Q(enrollments__is_active=True))
    )[:5]

    # Unified Upcoming Birthdays (next 30 days) from all profile types
    upcoming_birthdays = []
    today = timezone.localdate()
    
    # 1. Students
    student_birthdays = list(Student.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
    for item in student_birthdays:
        item['role'] = "O'quvchi"
    # 2. Teachers
    teacher_birthdays = list(Teacher.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
    for item in teacher_birthdays:
        item['role'] = "O'qituvchi"
    # 3. Admins
    from admins.models import AdminProfile
    admin_birthdays = list(AdminProfile.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
    for item in admin_birthdays:
        item['role'] = 'Admin'
    
    # Combined list
    all_raw_birthdays = student_birthdays + teacher_birthdays + admin_birthdays
    
    for item in all_raw_birthdays:
        bdate = item['birth_date']
        try:
            bday_this_year = bdate.replace(year=today.year)
        except ValueError: # Feb 29
            bday_this_year = bdate.replace(year=today.year, month=3, day=1)
            
        if bday_this_year < today:
            bday_this_year = bday_this_year.replace(year=today.year + 1)
            
        days_until = (bday_this_year - today).days
        if days_until <= 30:
            item['days_until_birthday'] = days_until
            upcoming_birthdays.append(item)
    
    upcoming_birthdays.sort(key=lambda x: x['days_until_birthday'])
    upcoming_birthdays = upcoming_birthdays[:5]

    # Check if today is the current user's birthday for the celebration effect
    user_birthday_today = False
    user_profile = None
    if request.user.is_authenticated:
        if request.user.role == 'student':
            user_profile = getattr(request.user, 'student_profile', None)
        elif request.user.role == 'teacher':
            user_profile = getattr(request.user, 'teacher_profile', None)
        elif request.user.role in ['admin', 'superadmin', 'accountant']:
            user_profile = getattr(request.user, 'admin_profile', None)
            
        if user_profile and user_profile.birth_date:
            bdate = user_profile.birth_date
            if bdate.month == today.month and bdate.day == today.day:
                user_birthday_today = True

    # Debtors list
    debtors_list = Payment.objects.filter(
        status__in=['unpaid', 'partial']
    ).select_related('student', 'group__course').order_by('-expected_amount')[:5]

    context = {
        'total_students': total_students,
        'total_groups': total_groups,
        'total_teachers': total_teachers,
        'monthly_income': monthly_income,
        'debtor_count': debtor_count,
        'total_debt': total_debt,
        'recent_payments': recent_payments,
        'recent_students': recent_students,
        'chart_months': chart_months,
        'chart_income': chart_income,
        'groups_with_counts': groups_with_counts,
        'upcoming_birthdays': upcoming_birthdays,
        'debtors_list': debtors_list,
        'user_birthday_today': user_birthday_today,
        'now': now,
    }
    return render(request, 'dashboard/home.html', context)
