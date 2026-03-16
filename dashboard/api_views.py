from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from students.models import Student
from teachers.models import Teacher
from admins.models import AdminProfile
from courses.models import Group
from payments.models import Payment

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        User = get_user_model()
        now = timezone.now()
        month = now.month
        year = now.year

        total_students = Student.objects.filter(status='active').count()
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

        # Generate chart data
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

        # Recent payments
        recent_payments_queryset = Payment.objects.select_related(
            'student', 'group__course'
        ).order_by('-created_at')[:5]
        
        recent_payments = []
        for p in recent_payments_queryset:
            recent_payments.append({
                'id': p.id,
                'student_name': p.student.get_full_name() if p.student else '',
                'student_first_char': p.student.first_name[0] if p.student and p.student.first_name else 'U',
                'group_name': p.group.name if p.group else '',
                'amount': p.amount,
                'status': p.status,
                'status_display': p.get_status_display()
            })

        # Groups with counts
        groups_qs = Group.objects.filter(is_active=True).select_related('course').annotate(
            enrolled=Count('enrollments', filter=Q(enrollments__is_active=True))
        )[:5]
        
        groups_with_counts = []
        for g in groups_qs:
            groups_with_counts.append({
                'id': g.id,
                'name': g.name,
                'course_name': g.course.name if g.course else '',
                'enrolled': g.enrolled,
                'max_students': g.max_students
            })

        # Debtors
        debtors_qs = Payment.objects.filter(
            status__in=['unpaid', 'partial']
        ).select_related('student', 'group__course').order_by('-expected_amount')[:5]
        
        debtors_list = []
        for p in debtors_qs:
            debtors_list.append({
                'id': p.id,
                'student_name': p.student.get_full_name() if p.student else '',
                'student_first_char': p.student.first_name[0] if p.student and p.student.first_name else 'U',
                'course_name': p.group.course.name if p.group and p.group.course else '',
                'remaining': p.remaining
            })

        # Upcoming birthdays
        upcoming_birthdays = []
        today = timezone.localdate()
        
        student_birthdays = list(Student.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
        for item in student_birthdays: item['role'] = "O'quvchi"
            
        teacher_birthdays = list(Teacher.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
        for item in teacher_birthdays: item['role'] = "O'qituvchi"
            
        admin_birthdays = list(AdminProfile.objects.exclude(birth_date__isnull=True).values('first_name', 'last_name', 'birth_date'))
        for item in admin_birthdays: item['role'] = 'Admin'

        all_raw_birthdays = student_birthdays + teacher_birthdays + admin_birthdays
        
        for item in all_raw_birthdays:
            bdate = item['birth_date']
            try:
                bday_this_year = bdate.replace(year=today.year)
            except ValueError:
                bday_this_year = bdate.replace(year=today.year, month=3, day=1)
                
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
                
            days_until = (bday_this_year - today).days
            if days_until <= 30:
                upcoming_birthdays.append({
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'first_char': item['first_name'][0] if item['first_name'] else 'U',
                    'role': item['role'],
                    'date_str': bdate.strftime('%d-%B'),
                    'days_until': days_until
                })
        
        upcoming_birthdays.sort(key=lambda x: x['days_until'])
        upcoming_birthdays = upcoming_birthdays[:5]

        return Response({
            'stats': {
                'total_students': total_students,
                'total_groups': total_groups,
                'total_teachers': total_teachers,
                'monthly_income': monthly_income,
                'debtor_count': debtor_count,
                'total_debt': total_debt,
            },
            'chart': {
                'labels': chart_months,
                'data': chart_income
            },
            'recent_payments': recent_payments,
            'groups_with_counts': groups_with_counts,
            'debtors_list': debtors_list,
            'upcoming_birthdays': upcoming_birthdays
        })
