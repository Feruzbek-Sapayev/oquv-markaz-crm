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
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            # Auto-set expected_amount from enrollment discount
            try:
                enrollment = Enrollment.objects.get(student=payment.student, group=payment.group, is_active=True)
                payment.expected_amount = enrollment.discounted_fee
            except Enrollment.DoesNotExist:
                payment.expected_amount = payment.group.course.monthly_fee
            payment.save()
            messages.success(request, "To'lov qo'shildi!")
            return redirect('payments:list')
    else:
        initial = {'student': selected_student} if selected_student else None
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
    """O'quvchilar who have unpaid or partial payments"""
    if request.user.is_admin_role:
        payments = Payment.objects.filter(status__in=['unpaid', 'partial'])
    elif request.user.is_teacher:
        payments = Payment.objects.filter(status__in=['unpaid', 'partial'], group__teacher__user=request.user).distinct()
    else:
        messages.error(request, "Qarzdorlar ro'yxatini ko'rish huquqingiz yo'q!")
        return redirect('dashboard:home')
    
    payments = payments.select_related('student', 'group__course').order_by('student__last_name')
    total_debt = payments.aggregate(t=Sum('expected_amount') - Sum('amount'))['t'] or 0

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(payments, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'payments/debtor_list.html', {'payments': page_obj, 'page_obj': page_obj, 'total_debt': total_debt})


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
        ["Kutilgan:", f"{payment.expected_amount:,.0f} so'm"],
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
    ws.append(["#", "O'quvchi", "Guruh", "Oy", "Yil", "To'lov", "Kutilgan", "Holat", "Usul", "Sana"])
    for i, p in enumerate(payments, 1):
        ws.append([
            i, str(p.student), str(p.group), p.month, p.year,
            float(p.amount), float(p.expected_amount),
            p.get_status_display(), p.get_method_display(), str(p.paid_at or '')
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=payments.xlsx"
    wb.save(response)
    return response
