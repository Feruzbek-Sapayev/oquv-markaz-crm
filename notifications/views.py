from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from .models import Notification
from .forms import MassNotificationForm
from accounts.models import CustomUser
from accounts.permissions import admin_required

@admin_required
def send_mass_notification(request):
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
            return redirect('dashboard:home')
    else:
        form = MassNotificationForm()
    
    return render(request, 'notifications/send_mass.html', {'form': form, 'title': "Xabar yuborish"})

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
            'created_at': n.created_at.strftime('%d.%m %H:%i')
        })
    return JsonResponse({'notifications': data})
