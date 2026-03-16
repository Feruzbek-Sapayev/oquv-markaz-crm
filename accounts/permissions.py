from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Ushbu sahifaga kirish uchun ruxsatingiz yo'q!")
            return redirect('dashboard:home')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_admin_role:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Ushbu amalni bajarish faqat adminlar uchun!")
        return redirect('dashboard:home')
    return _wrapped_view

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_teacher or request.user.is_admin_role):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Ushbu sahifa faqat o'qituvchilar uchun!")
        return redirect('dashboard:home')
    return _wrapped_view

def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_student or request.user.is_admin_role):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Ushbu sahifa faqat o'quvchilar uchun!")
        return redirect('dashboard:home')
    return _wrapped_view
