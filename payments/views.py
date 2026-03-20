from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import Payment
from .forms import PaymentForm
from students.models import Student
from courses.models import Enrollment, Group
from accounts.permissions import admin_required, teacher_required
import openpyxl
from io import BytesIO
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


@login_required
def payment_list(request):
    if request.user.is_admin_role:
        payments = Payment.objects.select_related('student', 'group__course', 'created_by').all()
    elif request.user.is_teacher:
        payments = Payment.objects.filter(group__teacher__user=request.user).select_related('student', 'group__course', 'created_by').distinct()
    elif request.user.is_student:
        payments = Payment.objects.filter(student__user=request.user).select_related('student', 'group__course', 'created_by')
    else:
        payments = Payment.objects.none()
    status = request.GET.get('status', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', str(timezone.now().year))
    query = request.GET.get('q', '')

    if status:
        payments = payments.filter(status=status)
    if month:
        payments = payments.filter(month=month)
    if year:
        payments = payments.filter(year=year)
    if query:
        payments = payments.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )

    total_income = payments.filter(status__in=['paid', 'partial']).aggregate(t=Sum('amount'))['t'] or 0

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(payments, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'payments': page_obj,
        'page_obj': page_obj,
        'status': status,
        'month': month,
        'year': year,
        'query': query,
        'total_income': total_income,
        'statuses': Payment.Status.choices,
        'months': range(1, 13),
        'years': range(2023, timezone.now().year + 2),
    }
    return render(request, 'payments/payment_list.html', context)


@admin_required
def payment_create(request):
    selected_student = None
    student_id = request.GET.get('student')
    if student_id:
        selected_student = Student.objects.filter(pk=student_id).first()
    
    group_id = request.GET.get('group')
    month = request.GET.get('month')
    year = request.GET.get('year')
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            # Auto-set expected_amount from enrollment specific month discount
            try:
                enrollment = Enrollment.objects.get(student=payment.student, group=payment.group, is_active=True)
                total_due_for_month = enrollment.get_discounted_fee_for_month(payment.month, payment.year)
                
                # If they pay in installments, calculate remaining for this month
                from django.db.models import Sum
                already_paid = Payment.objects.filter(
                    student=payment.student, 
                    group=payment.group, 
                    month=payment.month, 
                    year=payment.year
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                payment.expected_amount = max(0, total_due_for_month - already_paid)
            except (Enrollment.DoesNotExist):
                payment.expected_amount = payment.group.course.monthly_fee
            payment.save()
            messages.success(request, "To'lov qo'shildi!")
            return redirect('payments:list')
    else:
        initial = {}
        if selected_student: initial['student'] = selected_student
        if group_id: initial['group'] = group_id
        if month: initial['month'] = month
        if year: initial['year'] = year
        form = PaymentForm(initial=initial)
    return render(request, 'payments/payment_form.html', {'form': form, 'title': "Yangi to'lov"})


@admin_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "To'lov yangilandi!")
            return redirect('payments:list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'payments/payment_form.html', {'form': form, 'title': "To'lovni tahrirlash", 'obj': payment})


@admin_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, "To'lov o'chirildi!")
        return redirect('payments:list')
    return render(request, 'payments/payment_confirm_delete.html', {'obj': payment})


@login_required
def debtor_list(request):
    """Identify students who have overdue payments based on grace period"""
    from datetime import date
    import calendar
    from decimal import Decimal

    today = timezone.now().date()
    
    if request.user.is_admin_role:
        enrollments = Enrollment.objects.filter(is_active=True).select_related('student', 'group__course')
    elif request.user.is_teacher:
        enrollments = Enrollment.objects.filter(
            is_active=True, 
            group__teacher__user=request.user
        ).select_related('student', 'group__course')
    else:
        messages.error(request, "Qarzdorlar ro'yxatini ko'rish huquqingiz yo'q!")
        return redirect('dashboard:home')
    
    debtor_items = []
    total_debt_sum = 0

    for e in enrollments:
        group_start = e.group.start_date
        # skip if group is in its first month (current month <= group start month)
        if today.year * 12 + today.month <= group_start.year * 12 + group_start.month:
            continue

        # Start checking from enrollment month or group start month (whichever is later)
        # Actually logic says "guruh yaratilgan oydan katta bolsa" check all students in that group.
        # We start checking from the student's enrollment month.
        current_date = date(e.enrolled_at.year, e.enrolled_at.month, 1)
        
        while current_date <= date(today.year, today.month, 1):
            # Calculate due date for this month based on group start DAY
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            due_day = min(group_start.day, last_day)
            due_date = date(current_date.year, current_date.month, due_day)
            
            if today < due_date:
                break # Not yet due for this month
                
            # Check payment for this month (M/Y)
            expected = e.get_discounted_fee_for_month(current_date.month, current_date.year)
            
            # Aggregate all payments for this month (M/Y)
            payments_data = Payment.objects.filter(
                student=e.student, group=e.group,
                month=current_date.month, year=current_date.year
            ).aggregate(total_paid=Sum('amount'))
            
            paid = payments_data['total_paid'] or Decimal('0')
            remaining = expected - paid
            
            if remaining > 0:
                debtor_items.append({
                    'pk': None,
                    'student': e.student,
                    'group': e.group,
                    'month': current_date.month,
                    'year': current_date.year,
                    'amount': paid,
                    'expected_amount': expected,
                    'remaining': remaining,
                    'status': 'partial' if paid > 0 else 'unpaid',
                    'get_status_display': "Qisman to'langan" if paid > 0 else "To'lanmagan",
                })
                total_debt_sum += remaining
            
            # Advance to next month
            if current_date.month == 12:
                current_date = date(current_date.year+1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month+1, 1)

    # Sort by student name
    debtor_items.sort(key=lambda x: x['student'].last_name)

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(debtor_items, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    debtor_count = len(debtor_items)
    unpaid_count = len([x for x in debtor_items if x['status'] == 'unpaid'])
    partial_count = len([x for x in debtor_items if x['status'] == 'partial'])

    return render(request, 'payments/debtor_list.html', {
        'payments': page_obj, 
        'page_obj': page_obj, 
        'total_debt': total_debt_sum,
        'debtor_count': debtor_count,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
    })


@login_required
def payment_pdf(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('student', 'group__course', 'created_by'), pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_student and payment.student.user != request.user:
            messages.error(request, "Boshqa o'quvchining chekini ko'ra olmaysiz!")
            return redirect('dashboard:home')
        if request.user.is_teacher and payment.group.teacher.user != request.user:
            messages.error(request, "Faqat o'z guruhlaringiz to'lovlarini ko'ra olasiz!")
            return redirect('dashboard:home')
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>O'QUV MARKAZ - TO'LOV CHEKI</b>", styles['Title']))
    elements.append(Spacer(1, 0.3*cm))

    data = [
        ["O'quvchi:", str(payment.student)],
        ["Guruh:", str(payment.group)],
        ["Kurs:", payment.group.course.name],
        ["Oy/Yil:", f"{payment.month}/{payment.year}"],
        ["To'lov miqdori:", f"{payment.amount:,.0f} so'm"],
        ["Qoldiq:", f"{payment.remaining:,.0f} so'm"],
        ["Holat:", payment.get_status_display()],
        ["Usul:", payment.get_method_display()],
        ["Sana:", str(payment.paid_at or '-')],
        ["Qo'shgan:", str(payment.created_by or '-')],
    ]

    table = Table(data, colWidths=[4*cm, 9*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Chek raqami: #{payment.pk} | {timezone.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=payment_{payment.pk}.pdf'
    return response


@admin_required
def payment_export_excel(request):
    payments = Payment.objects.select_related('student', 'group__course').all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "To'lovlar"
    ws.append(["#", "O'quvchi", "Guruh", "Oy", "Yil", "To'lov", "Holat", "Usul", "Sana"])
    for i, p in enumerate(payments, 1):
        ws.append([
            i, str(p.student), str(p.group), p.month, p.year,
            float(p.amount),
            p.get_status_display(), p.get_method_display(), str(p.paid_at or '')
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=payments.xlsx"
    wb.save(response)
    return response
