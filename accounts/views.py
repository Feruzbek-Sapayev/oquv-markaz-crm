from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from .models import CustomUser
from .forms import CustomUserForm
from django.contrib.auth.forms import AuthenticationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Username yoki parol noto\'g\'ri!')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Tizimdan chiqildi.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    profile = None
    profile_type = None

    if user.role == 'student':
        profile = getattr(user, 'student_profile', None)
        profile_type = 'student'
    elif user.role == 'teacher':
        profile = getattr(user, 'teacher_profile', None)
        profile_type = 'teacher'
    elif user.role in ['admin', 'superadmin', 'accountant']:
        profile = getattr(user, 'admin_profile', None)
        profile_type = 'admin'

    context = {
        'profile': profile,
        'profile_type': profile_type,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    from admins.models import AdminProfile
    from teachers.models import Teacher
    from students.models import Student

    user = request.user
    profile = None

    if user.role == 'student':
        profile = getattr(user, 'student_profile', None)
    elif user.role == 'teacher':
        profile = getattr(user, 'teacher_profile', None)
    elif user.role in ['admin', 'superadmin', 'accountant']:
        profile = getattr(user, 'admin_profile', None)
        if not profile:
            profile = AdminProfile.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
            )

    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        user.save()

        # Update profile fields
        if profile:
            profile.first_name = user.first_name
            profile.last_name = user.last_name
            profile.phone = user.phone
            birth_date = request.POST.get('birth_date')
            if birth_date:
                profile.birth_date = birth_date
            if hasattr(profile, 'middle_name'):
                profile.middle_name = request.POST.get('middle_name', profile.middle_name)
            if hasattr(profile, 'address'):
                profile.address = request.POST.get('address', profile.address)
            if request.FILES.get('photo'):
                profile.photo = request.FILES['photo']
            profile.save()

        messages.success(request, 'Profil muvaffaqiyatli yangilandi!')
        return redirect('accounts:profile')

    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def user_list(request):
    if not request.user.is_admin_role:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    users = CustomUser.objects.all().order_by('role', 'username')
    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 20

    paginator = Paginator(users, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'accounts/user_list.html', {'users': page_obj, 'page_obj': page_obj})




@login_required
def user_create(request):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Handle profile linking
            role = form.cleaned_data.get('role')
            if role == 'teacher':
                profile = form.cleaned_data.get('teacher_profile')
                if profile:
                    profile.user = user
                    profile.save()
            elif role == 'student':
                profile = form.cleaned_data.get('student_profile')
                if profile:
                    profile.user = user
                    profile.save()
            messages.success(request, 'Foydalanuvchi muvaffaqiyatli qo\'shildi!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Yangi foydalanuvchi'})


@login_required
def user_edit(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    user = CustomUser.objects.get(pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            # Handle profile linking
            role = form.cleaned_data.get('role')
            if role == 'teacher':
                profile = form.cleaned_data.get('teacher_profile')
                # Unlink old
                Teacher.objects.filter(user=user).update(user=None)
                if profile:
                    profile.user = user
                    profile.save()
            elif role == 'student':
                profile = form.cleaned_data.get('student_profile')
                # Unlink old
                Student.objects.filter(user=user).update(user=None)
                if profile:
                    profile.user = user
                    profile.save()
            messages.success(request, 'Foydalanuvchi tahrirlandi!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Tahrirlash', 'obj': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    user = CustomUser.objects.get(pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Foydalanuvchi o\'chirildi!')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'obj': user})
