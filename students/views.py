from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Student
from .forms import StudentForm
from accounts.permissions import admin_required, teacher_required
from courses.models import Enrollment, Group, Course, Exam
from courses.forms import ExamForm
from teachers.models import Teacher
from payments.models import Payment
from datetime import date
import openpyxl
from django.http import HttpResponse

@login_required
@teacher_required # Or admin
def add_exam(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Imtihon bali saqlandi!")
            return redirect('students:detail', pk=student_id)
    return redirect('students:detail', pk=student_id)


@login_required
def student_list(request):
    if request.user.is_admin_role:
        students = Student.objects.all()
    elif request.user.is_teacher:
        students = Student.objects.filter(enrollments__group__teacher__user=request.user).distinct()
    else:
        messages.error(request, "Sizda o'quvchilar ro'yxatini ko'rish huquqi yo'q!")
        return redirect('dashboard:home')

    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    course_id = request.GET.get('course', '')
    group_id = request.GET.get('group', '')
    teacher_id = request.GET.get('teacher', '')
    payment_status = request.GET.get('payment_status', '')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query)
        )
    if status:
        students = students.filter(status=status)
    if course_id:
        students = students.filter(enrollments__group__course_id=course_id)
    if group_id:
        students = students.filter(enrollments__group_id=group_id)
    if teacher_id:
        students = students.filter(enrollments__group__teacher_id=teacher_id)
    if payment_status:
        today = date.today()
        students = students.filter(
            payments__status=payment_status,
            payments__month=today.month,
            payments__year=today.year
        )
        
    students = students.distinct()

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(students, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    courses_qs = Course.objects.all()
    groups_qs = Group.objects.all()
    teachers_qs = Teacher.objects.filter(status='active')

    if course_id:
        groups_qs = groups_qs.filter(course_id=course_id)
        teachers_qs = teachers_qs.filter(groups__course_id=course_id).distinct()
    if teacher_id:
        courses_qs = courses_qs.filter(groups__teacher_id=teacher_id).distinct()
        groups_qs = groups_qs.filter(teacher_id=teacher_id).distinct()
    if group_id:
        selected_grp = get_object_or_404(Group, pk=group_id)
        # If group is selected, we can lock course and filter teachers of that course
        if not course_id:
            courses_qs = courses_qs.filter(pk=selected_grp.course_id)
        teachers_qs = teachers_qs.filter(groups__course_id=selected_grp.course_id).distinct()

    context = {
        'students': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'statuses': Student.Status.choices,
        'courses': courses_qs,
        'groups': groups_qs,
        'teachers': teachers_qs,
        'payment_statuses': Payment.Status.choices,
        'selected_course': course_id,
        'selected_group': group_id,
        'selected_teacher': teacher_id,
        'selected_payment_status': payment_status,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_teacher:
            if not student.enrollments.filter(group__teacher__user=request.user).exists():
                messages.error(request, "Ushbu o'quvchi ma'lumotlarini ko'rish huquqingiz yo'q!")
                return redirect('students:list')
        elif request.user.is_student:
            if student.user != request.user:
                messages.error(request, "Faqat o'z ma'lumotlaringizni ko'rishingiz mumkin!")
                return redirect('dashboard:home')
        else:
            return redirect('dashboard:home')

    enrollments = student.enrollments.select_related('group__course').all().order_by('-enrolled_at')
    payments = student.payments.select_related('group__course').order_by('-year', '-month')
    attendances = student.attendances.select_related('session__group').order_by('-session__date')[:20]
    
    # Progress Chart Data
    exams = student.exams.select_related('group').order_by('date')
    chart_labels = [e.date.strftime('%d.%m') for e in exams]
    chart_data = [e.score for e in exams]
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'attendances': attendances,
        'exams': exams,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'exam_form': ExamForm(initial={'student': student}),
    }
    return render(request, 'students/student_detail.html', context)


@admin_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"{student} muvaffaqiyatli qo'shildi!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'title': "Yangi o'quvchi"})


@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "O'quvchi ma'lumotlari yangilandi!")
            return redirect('students:detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'title': "Tahrirlash", 'obj': student})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if not request.user.is_admin_role:
        messages.error(request, "Ruxsatingiz yo'q!")
        return redirect('students:list')
    if request.method == 'POST':
        student.delete()
        messages.success(request, "O'quvchi o'chirildi!")
        return redirect('students:list')
    return render(request, 'students/student_confirm_delete.html', {'obj': student})


@admin_required
def student_export_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "O'quvchilar"
    headers = ["#", "Ism", "Familiya", "Telefon", "Jins", "Holat", "Ro'yxat sanasi"]
    ws.append(headers)
    for i, s in enumerate(Student.objects.all(), 1):
        ws.append([i, s.first_name, s.last_name, s.phone, s.get_gender_display(), s.get_status_display(), str(s.registered_at)])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=students.xlsx"
    wb.save(response)
    return response
