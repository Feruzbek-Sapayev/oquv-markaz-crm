from django.utils import timezone
from datetime import timedelta
from students.models import Student
from teachers.models import Teacher
from admins.models import AdminProfile
from courses.models import Group

def birthday_context(request):
    if not request.user.is_authenticated:
        return {}

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()
    user_birthday_today = False
    profile = None

    if request.user.role == 'student':
        profile = getattr(request.user, 'student_profile', None)
    elif request.user.role == 'teacher':
        profile = getattr(request.user, 'teacher_profile', None)
    elif request.user.role in ['admin', 'superadmin', 'accountant']:
        profile = getattr(request.user, 'admin_profile', None)

    if profile and profile.birth_date:
        if profile.birth_date.month == today.month and profile.birth_date.day == today.day:
            user_birthday_today = True

    # Calculate upcoming class
    upcoming_class = None
    best_dt = None

    groups = Group.objects.filter(is_active=True)
    if hasattr(request.user, 'role'):
        if request.user.role == 'student':
            groups = groups.filter(enrollments__student__user=request.user, enrollments__is_active=True).distinct()
        elif request.user.role == 'teacher':
            groups = groups.filter(teacher__user=request.user).distinct()

    days_map = {
        'odd': [0, 2, 4],
        'even': [1, 3, 5],
        'daily': [0, 1, 2, 3, 4, 5, 6],
        'weekend': [5, 6]
    }

    for g in groups:
        allowed_days = days_map.get(g.days, [])
        if not allowed_days:
            continue
        
        for offset in range(14):
            check_date = today + timedelta(days=offset)
            if check_date.weekday() in allowed_days:
                if offset == 0:
                    if current_time < g.end_time: # Hasn't ended today
                        dt = timezone.make_aware(timezone.datetime.combine(check_date, g.start_time))
                        if best_dt is None or dt < best_dt:
                            best_dt = dt
                            upcoming_class = g
                        break
                else:
                    dt = timezone.make_aware(timezone.datetime.combine(check_date, g.start_time))
                    if best_dt is None or dt < best_dt:
                        best_dt = dt
                        upcoming_class = g
                    break

    return {
        'user_birthday_today': user_birthday_today,
        'user_profile_for_bday': profile,
        'upcoming_class': upcoming_class,
        'upcoming_class_dt': best_dt,
    }
