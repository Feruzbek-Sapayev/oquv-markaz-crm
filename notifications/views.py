from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from django.core.paginator import Paginator
from .models import Notification
from .forms import MassNotificationForm
from accounts.models import CustomUser
from accounts.permissions import admin_required

@login_required
def send_group_notification(request, group_pk):
    from courses.models import Group
    group = get_object_or_404(Group, pk=group_pk)
    
    # Permission check: admin or group teacher
    if not (request.user.is_admin_role or (request.user.is_teacher and group.teacher and group.teacher.user == request.user)):
        messages.error(request, "Xabar yuborish huquqingiz yo'q!")
        return redirect('courses:group_detail', pk=group_pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        if title and message:
            # Get all active students with associated user accounts
            enrollments = group.enrollments.filter(status='active').select_related('student__user')
            recipients = [e.student.user for e in enrollments if e.student.user]
            
            if recipients:
                notification_objs = [
                    Notification(
                        recipient=user,
                        sender=request.user,
                        title=title,
                        message=message
                    ) for user in recipients
                ]
                Notification.objects.bulk_create(notification_objs)
                messages.success(request, f"{len(recipients)} ta o'quvchiga xabar yuborildi!")
            else:
                messages.warning(request, "Guruhda xabar yuborilishi mumkin bo'lgan faol o'quvchilar yo'q.")
        else:
            messages.error(request, "Sarlavha va xabar to'ldirilishi shart!")
            
    return redirect('courses:group_detail', pk=group_pk)


@admin_required
def send_mass_notification(request):
    sent_messages_qs = Notification.objects.filter(sender=request.user).select_related('recipient').order_by('-created_at')
    
    sort = request.GET.get('sort', '')
    if sort == 'status_asc':
        sent_messages_qs = sent_messages_qs.order_by('is_read', '-created_at')
    elif sort == 'status_desc':
        sent_messages_qs = sent_messages_qs.order_by('-is_read', '-created_at')
    elif sort == 'date_asc':
        sent_messages_qs = sent_messages_qs.order_by('created_at')
    elif sort == 'date_desc':
        sent_messages_qs = sent_messages_qs.order_by('-created_at')

    page_size = request.GET.get('page_size', 20)
    try:
        page_size = int(page_size)
    except (ValueError, TypeError):
        page_size = 20

    paginator = Paginator(sent_messages_qs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = MassNotificationForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            
            recipients = []
            if recipient_type == 'all':
                recipients = CustomUser.objects.all()
            elif recipient_type in ['teacher', 'student', 'admin']:
                recipients = CustomUser.objects.filter(role=recipient_type)
            elif recipient_type == 'specific':
                recipients = form.cleaned_data['specific_users']
            
            # Create notifications
            notification_objs = [
                Notification(
                    recipient=user,
                    sender=request.user,
                    title=title,
                    message=message
                ) for user in recipients
            ]
            Notification.objects.bulk_create(notification_objs)
            
            messages.success(request, f"{len(recipients)} ta foydalanuvchiga xabar yuborildi!")
            return redirect('notifications:send_mass')
    else:
        form = MassNotificationForm()
    
    return render(request, 'notifications/send_mass.html', {
        'form': form, 
        'title': "Xabarlar",
        'page_obj': page_obj,
        'sent_messages': page_obj
    })

@login_required
def notification_list(request):
    user_notifications = request.user.notifications.all()
    # Mark all as read when viewing list? Or let user do it individually?
    # For now, just list.
    return render(request, 'notifications/list.html', {
        'notifications': user_notifications,
        'title': "Mening xabarlarim"
    })

@login_required
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def mark_all_as_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

def get_unread_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def get_recent_notifications(request):
    notifications = request.user.notifications.all()[:5]
    data = []
    for n in notifications:
        data.append({
            'pk': n.pk,
            'title': n.title,
            'message': n.message[:50] + '...' if len(n.message) > 50 else n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d.%m %H:%M')
        })
    return JsonResponse({'notifications': data})

@login_required
def resend_notification(request, pk):
    original = get_object_or_404(Notification, pk=pk, sender=request.user)
    Notification.objects.create(
        recipient=original.recipient,
        sender=request.user,
        title=original.title,
        message=original.message
    )
    messages.success(request, f"Xabar {original.recipient.get_full_name()} ga qayta yuborildi!")
    return redirect('notifications:send_mass')
