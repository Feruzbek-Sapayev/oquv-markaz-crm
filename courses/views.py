from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Course, Room, Group, Enrollment, Exam, GroupDiscount
from .forms import CourseForm, RoomForm, GroupForm, EnrollmentForm, ExamForm, GroupDiscountForm, EnrollmentUpdateForm
from accounts.permissions import admin_required, teacher_required
import openpyxl
from django.http import HttpResponse
import datetime
import calendar
from django.utils import timezone
from attendance.models import Attendance, AttendanceSession, DailyGrade


# ──────────── COURSES ────────────
@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    groups = course.groups.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'groups': groups
    })

@admin_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"'{course.name}' kursi saqlandi!")
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {
        'form': form, 
        'title': 'Yangi kurs'
    })

@admin_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Kurs ma'lumotlari yangilandi!")
            return redirect('courses:course_detail', pk=pk)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {
        'form': form, 
        'title': 'Tahrirlash', 
        'obj': course
    })


@admin_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Kurs o\'chirildi!')
        return redirect('courses:course_list')
    return render(request, 'courses/confirm_delete.html', {'obj': course, 'title': 'Kursni o\'chirish'})


# ──────────── ROOMS ────────────
@login_required
def room_list(request):
    rooms = Room.objects.all()
    return render(request, 'courses/room_list.html', {'rooms': rooms})

@admin_required
def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"'{room.name}' xonasi saqlandi!")
            return redirect('courses:room_list')
    else:
        form = RoomForm()
    return render(request, 'courses/room_form.html', {
        'form': form, 
        'title': 'Yangi xona'
    })

@admin_required
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Xona ma'lumotlari yangilandi!")
            return redirect('courses:room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'courses/room_form.html', {
        'form': form, 
        'title': 'Tahrirlash', 
        'obj': room
    })

@admin_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Xona o\'chirildi!')
        return redirect('courses:room_list')
    return render(request, 'courses/confirm_delete.html', {'obj': room, 'title': 'Xonani o\'chirish'})


# ──────────── GROUPS ────────────
@login_required
def group_list(request):
    if request.user.is_admin_role:
        groups = Group.objects.select_related('course').all()
    elif request.user.is_teacher:
        groups = Group.objects.filter(teacher__user=request.user).select_related('course').distinct()
    elif request.user.is_student:
        groups = Group.objects.filter(enrollments__student__user=request.user, enrollments__is_active=True).select_related('course').distinct()
    else:
        groups = Group.objects.none()

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(groups, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'courses/group_list.html', {'groups': page_obj, 'page_obj': page_obj})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group.objects.select_related('course'), pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_teacher and group.teacher.user != request.user:
            messages.error(request, "Bu guruhga kirish huquqingiz yo'q!")
            return redirect('courses:group_list')
        if request.user.is_student and not group.enrollments.filter(student__user=request.user, is_active=True).exists():
            messages.error(request, "Siz ushbu guruhga a'zo emassiz!")
            return redirect('courses:group_list')

    # Specific ordering: 1. Active, 2. Inactive, 3. Graduated
    from django.db.models import Case, When, Value, IntegerField
    enrollments = group.enrollments.select_related('student').annotate(
        status_order=Case(
            When(status=Enrollment.Status.ACTIVE, then=Value(1)),
            When(status=Enrollment.Status.INACTIVE, then=Value(2)),
            When(status=Enrollment.Status.GRADUATED, then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by('status_order', 'student__last_name')

    # Attendance Matrix Logic
    today = timezone.now().date()
    month_year = request.GET.get('month_year')
    month = request.GET.get('month')
    year = request.GET.get('year')

    try:
        if month_year and '-' in month_year:
            parts = month_year.split('-')
            month = int(parts[0])
            year = int(parts[1])
        else:
            month = int(month) if month else today.month
            year = int(year) if year else today.year
    except (ValueError, TypeError, IndexError):
        month, year = today.month, today.year
        
    start_date = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime.date(year, month, last_day)
    
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    potential_dates = [start_date + datetime.timedelta(days=i) for i in range(last_day)]
    schedule = group.days
    if schedule == Group.DayChoices.ODD:
        all_dates = [d for d in potential_dates if d.weekday() in [0, 2, 4]]
    elif schedule == Group.DayChoices.EVEN:
        all_dates = [d for d in potential_dates if d.weekday() in [1, 3, 5]]
    elif schedule == Group.DayChoices.WEEKEND:
        all_dates = [d for d in potential_dates if d.weekday() in [5, 6]]
    else:
        all_dates = potential_dates
        
    attendance_records = Attendance.objects.filter(
        session__group=group, session__date__range=[start_date, end_date]
    ).values('student_id', 'session__date', 'status')

    # Session map: 'YYYY-MM-DD' → {pk, topic} for the Mavzu row
    sessions_qs = AttendanceSession.objects.filter(
        group=group, date__range=[start_date, end_date]
    ).values('pk', 'date', 'topic')
    session_map = {s['date'].strftime('%Y-%m-%d'): {'pk': s['pk'], 'topic': s['topic'] or ''} for s in sessions_qs}

    
    attendance_map = {}
    for r in attendance_records:
        sid, d, s = r['student_id'], r['session__date'], r['status']
        if sid not in attendance_map: attendance_map[sid] = {}
        attendance_map[sid][d] = s
        
    # Grade Records Logic
    grade_records = DailyGrade.objects.filter(
        session__group=group, session__date__range=[start_date, end_date]
    ).values('student_id', 'session__date', 'score')
    
    grade_map = {}
    for r in grade_records:
        sid, d, s = r['student_id'], r['session__date'], r['score']
        if sid not in grade_map: grade_map[sid] = {}
        grade_map[sid][d] = s

    matrix_data = []
    total_present = 0
    total_absent = 0
    total_records = 0
    
    for e in enrollments:
        student_atts = []
        student_grades = []
        present_count = 0
        absent_count = 0
        total_with_status = 0
        for d in all_dates:
            # Attendance
            status = attendance_map.get(e.student.pk, {}).get(d)
            student_atts.append({'date': d, 'status': status})
            if status:
                total_with_status += 1
                if status == Attendance.Status.PRESENT:
                    present_count += 1
                    total_present += 1
                    total_records += 1
                elif status == Attendance.Status.ABSENT:
                    absent_count += 1
                    total_absent += 1
                    total_records += 1
            
            # Grades
            score = grade_map.get(e.student.pk, {}).get(d)
            student_grades.append({'date': d, 'score': score})
        
        percent = (present_count / total_with_status * 100) if total_with_status else 0
        matrix_data.append({
            'student': e.student,
            'attendances': student_atts,
            'grades': student_grades,
            'present_count': present_count,
            'absent_count': absent_count,
            'percentage': round(percent),
        })
        
    overall_percentage = round((total_present / total_records * 100)) if total_records > 0 else 0

    # Months that actually have attendance sessions for this group
    session_month_tuples = (
        AttendanceSession.objects.filter(group=group)
        .dates('date', 'month')
        .values_list('date__year', 'date__month')
        .distinct()
        .order_by('date__year', 'date__month')
    )
    
    UZ_MONTHS = {
        1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
        5: 'May', 6: 'Iyun', 7: 'Iyul', 8: 'Avgust',
        9: 'Sentabr', 10: 'Oktabr', 11: 'Noyabr', 12: 'Dekabr'
    }
    
    # Build list of (value, label) for the select — only months with sessions
    session_months_qs = (
        AttendanceSession.objects.filter(group=group)
        .dates('date', 'month')
    )
    session_months = []
    for d in session_months_qs:
        session_months.append({
            'value': f"{d.month}-{d.year}",
            'label': f"{UZ_MONTHS[d.month]} {d.year}",
            'month': d.month,
            'year': d.year,
        })
    
    # Determine if a next month with sessions exists
    has_next_sessions = AttendanceSession.objects.filter(
        group=group,
        date__year=next_year,
        date__month=next_month
    ).exists()

    # Discount Logic
    month_choices = []
    curr = datetime.date(group.start_date.year, group.start_date.month, 1)
    for _ in range(group.course.duration_months):
        month_choices.append((f"{curr.month}-{curr.year}", f"{UZ_MONTHS[curr.month]} {curr.year}"))
        if curr.month == 12: curr = datetime.date(curr.year + 1, 1, 1)
        else: curr = datetime.date(curr.year, curr.month + 1, 1)

    enrollment_form = EnrollmentForm(group=group)

    discount_form = GroupDiscountForm(group=group)
    
    discounts = GroupDiscount.objects.filter(enrollment__group=group).select_related('enrollment__student')

    return render(request, 'courses/group_detail.html', {
        'group': group,
        'enrollments': enrollments,
        'matrix_data': matrix_data,
        'all_dates': all_dates,
        'current_month': month,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'stats': {
            'present': total_present,
            'absent': total_absent,
            'percent': overall_percentage,
        },
        'session_months': session_months,
        'has_next_sessions': has_next_sessions,
        'session_map': session_map,
        'enrollment_form': enrollment_form,
        'discount_form': discount_form,
        'discounts': discounts,
        'full_uz_months': [
            (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'), (5, 'May'), (6, 'Iyun'),
            (7, 'Iyul'), (8, 'Avgust'), (9, 'Sentabr'), (10, 'Oktabr'), (11, 'Noyabr'), (12, 'Dekabr')
        ],
    })

@login_required
def discount_create(request):
    if request.method == 'POST':
        # First, try to get enrollment to know how to filter month choices
        enrollment_id = request.POST.get('enrollment')
        if not enrollment_id:
            messages.error(request, "O'quvchi tanlanmagan!")
            return redirect('courses:group_list')
            
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        group = enrollment.group
        
        # Populate month choices same way as in detail view
        month_choices = []
        curr = datetime.date(group.start_date.year, group.start_date.month, 1)
        for _ in range(group.course.duration_months):
            month_choices.append((f"{curr.month}-{curr.year}", f"{curr.month}-{curr.year}")) # val doesn't matter for label here
            if curr.month == 12: curr = datetime.date(curr.year + 1, 1, 1)
            else: curr = datetime.date(curr.year, curr.month + 1, 1)
            
        form = GroupDiscountForm(request.POST)
        form.fields['month_year'].choices = month_choices # Set valid choices for validation
        
        if form.is_valid():
            discount = form.save(commit=False)
            my = form.cleaned_data['month_year'].split('-')
            discount.month = int(my[0])
            discount.year = int(my[1])
            discount.save()
            messages.success(request, f"{discount.enrollment.student} uchun chegirma saqlandi!")
            return redirect('courses:group_detail', pk=group.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('courses:group_detail', pk=group.pk)
    return redirect('courses:group_list')

@login_required
def discount_delete(request, pk):
    discount = get_object_or_404(GroupDiscount, pk=pk)
    group_pk = discount.enrollment.group.pk
    discount.delete()
    messages.success(request, "Chegirma o'chirildi!")
    return redirect('courses:group_detail', pk=group_pk)


@admin_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f"'{group.name}' guruhi yaratildi!")
            return redirect('courses:group_list')
    else:
        form = GroupForm()
    return render(request, 'courses/group_form.html', {'form': form, 'title': 'Yangi guruh'})


@teacher_required
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizni tahrirlashingiz mumkin!")
        return redirect('courses:group_list')
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guruh yangilandi!')
            return redirect('courses:group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'courses/group_form.html', {'form': form, 'title': 'Guruhni tahrirlash', 'obj': group})


@teacher_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizni o'chirishingiz mumkin!")
        return redirect('courses:group_list')
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Guruh o\'chirildi!')
        return redirect('courses:group_list')
    return render(request, 'courses/confirm_delete.html', {'obj': group, 'title': 'Guruhni o\'chirish'})


@teacher_required
def enrollment_create(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizga o'quvchi qo'shishingiz mumkin!")
        return redirect('courses:group_list')
        
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, group=group)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.group = group
            enrollment.save()
            messages.success(request, f"{enrollment.student} guruhga qo'shildi!")
            return redirect('courses:group_detail', pk=group_pk)
        else:
            for field, errors in form.errors.items():
                for dict_err in errors:
                    messages.error(request, f"{field}: {dict_err}")
    return redirect('courses:group_detail', pk=group_pk)


@teacher_required
def enrollment_edit(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    group_pk = enrollment.group.pk
    
    if not request.user.is_admin_role and enrollment.group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizdagi o'quvchilarni tahrirlashingiz mumkin!")
        return redirect('courses:group_detail', pk=group_pk)
        
    if request.method == 'POST':
        form = EnrollmentUpdateForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, f"{enrollment.student} ma'lumotlari yangilandi!")
            return redirect('courses:group_detail', pk=group_pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field or ''}: {error}")
            return redirect('courses:group_detail', pk=group_pk)
    else:
        form = EnrollmentUpdateForm(instance=enrollment)
    
    return render(request, 'courses/enrollment_form.html', {
        'form': form,
        'group': enrollment.group,
        'enrollment': enrollment,
        'title': "O'quvchi ma'lumotlarini tahrirlash"
    })

@teacher_required
def enrollment_remove(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    group_pk = enrollment.group.pk
    
    if not request.user.is_admin_role and enrollment.group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizdan o'quvchi chiqarishingiz mumkin!")
        return redirect('courses:group_detail', pk=group_pk)
    if request.method == 'POST':
        enrollment.delete() # Real delete if requested, or keep status based
        messages.success(request, "O'quvchi guruhdan o'chirildi!")
    return redirect('courses:group_detail', pk=group_pk)


@login_required
def group_export_excel(request, pk):
    group = get_object_or_404(Group, pk=pk)
    enrollments = group.enrollments.filter(is_active=True).select_related('student')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = group.name
    ws.append(["#", "Ism", "Familiya", "Telefon", "Chegirma (%)", "Qo'shilgan sana"])
    for i, e in enumerate(enrollments, 1):
        ws.append([i, e.student.first_name, e.student.last_name, e.student.phone, e.discount_percent, str(e.enrolled_at)])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=group_{group.name}.xlsx'
    wb.save(response)
    return response
@login_required
def lesson_schedule(request):
    # Determine which groups to show based on role
    if request.user.is_admin_role:
        groups = Group.objects.filter(is_active=True).select_related('course')
    elif request.user.is_teacher:
        groups = Group.objects.filter(
            is_active=True,
            teacher__user=request.user
        ).select_related('course').distinct()
    elif request.user.is_student:
        groups = Group.objects.filter(
            is_active=True,
            enrollments__student__user=request.user,
            enrollments__is_active=True
        ).select_related('course').distinct()
    else:
        groups = Group.objects.none()
    
    # Organize groups by day
    # We'll use day names in Uzbek for the frontend
    days_map = [
        ('Monday', 'Dushanba'),
        ('Tuesday', 'Seshanba'),
        ('Wednesday', 'Chorshanba'),
        ('Thursday', 'Payshanba'),
        ('Friday', 'Juma'),
        ('Saturday', 'Shanba'),
        ('Sunday', 'Yakshanba'),
    ]
    
    schedule = {day[1]: [] for day in days_map}
    
    for group in groups:
        if group.days == Group.DayChoices.ODD:
            schedule['Dushanba'].append(group)
            schedule['Chorshanba'].append(group)
            schedule['Juma'].append(group)
        elif group.days == Group.DayChoices.EVEN:
            schedule['Seshanba'].append(group)
            schedule['Payshanba'].append(group)
            schedule['Shanba'].append(group)
        elif group.days == Group.DayChoices.DAILY:
            for day in schedule:
                schedule[day].append(group)
        elif group.days == Group.DayChoices.WEEKEND:
            schedule['Shanba'].append(group)
            schedule['Yakshanba'].append(group)
            
    # Sort each day by start_time
    for day in schedule:
        schedule[day].sort(key=lambda x: x.start_time)
        
    # Room-based schedule for unified view with aligned rows
    room_objs = list(Room.objects.filter(is_active=True).order_by('name'))
    
    room_data_list = []
    
    def get_group_schedule(group):
        """Returns a list of 7 items (group or None) for each day."""
        sched = []
        for d_info in days_map:
            day_name = d_info[1]
            has_lesson = False
            if group.days == Group.DayChoices.ODD:
                has_lesson = day_name in ['Dushanba', 'Chorshanba', 'Juma']
            elif group.days == Group.DayChoices.EVEN:
                has_lesson = day_name in ['Seshanba', 'Payshanba', 'Shanba']
            elif group.days == Group.DayChoices.DAILY:
                has_lesson = True
            elif group.days == Group.DayChoices.WEEKEND:
                has_lesson = day_name in ['Shanba', 'Yakshanba']
            
            sched.append(group if has_lesson else None)
        return sched

    for room in room_objs:
        groups_in_room = [g for g in groups if g.room == room]
        groups_in_room.sort(key=lambda x: x.start_time)
        
        rows = []
        for g in groups_in_room:
            rows.append({
                'group': g,
                'days_schedule': get_group_schedule(g)
            })
        room_data_list.append({
            'room': room,
            'rows': rows
        })

    # Groups without a room
    no_room_groups = [g for g in groups if not g.room]
    no_room_groups.sort(key=lambda x: x.start_time)
    no_room_rows = []
    for g in no_room_groups:
        no_room_rows.append({
            'group': g,
            'days_schedule': get_group_schedule(g)
        })

    context = {
        'room_data_list': room_data_list,
        'no_room_rows': no_room_rows,
        'days': [day[1] for day in days_map],
        'title': 'Dars Jadvali'
    }
    return render(request, 'courses/schedule.html', context)
