from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Teacher
from .forms import TeacherForm
from accounts.permissions import admin_required, teacher_required
from courses.models import Group, Course


@admin_required
def teacher_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    teachers = Teacher.objects.all()
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    if status:
        teachers = teachers.filter(status=status)

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(teachers, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'teachers': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'statuses': Teacher.Status.choices,
    }
    return render(request, 'teachers/teacher_list.html', context)


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if teacher.user != request.user:
            messages.error(request, "Ushbu sahifani ko'rish huquqingiz yo'q!")
            return redirect('dashboard:home')

    groups = teacher.groups.select_related('course').order_by('-is_active', 'name')
    context = {
        'teacher': teacher,
        'groups': groups,
    }
    return render(request, 'teachers/teacher_detail.html', context)


@admin_required
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f"{teacher} muvaffaqiyatli qo'shildi!")
            return redirect('teachers:detail', pk=teacher.pk)
    else:
        form = TeacherForm()
    return render(request, 'teachers/teacher_form.html', {'form': form, 'title': "Yangi o'qituvchi"})


@admin_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "O'qituvchi ma'lumotlari yangilandi!")
            return redirect('teachers:detail', pk=pk)
    else:
        form = TeacherForm(instance=teacher)
    return render(request, 'teachers/teacher_form.html', {'form': form, 'title': "Tahrirlash", 'obj': teacher})


@login_required
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if not request.user.is_admin_role:
        messages.error(request, "Ruxsatingiz yo'q!")
        return redirect('teachers:list')
    if request.method == 'POST':
        teacher.delete()
        messages.success(request, "O'qituvchi o'chirildi!")
        return redirect('teachers:list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'obj': teacher})
