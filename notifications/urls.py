from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('send-mass/', views.send_mass_notification, name='send_mass'),
    path('my-notifications/', views.notification_list, name='list'),
    path('mark-read/<uuid:pk>/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    path('recent-notifications/', views.get_recent_notifications, name='recent_notifications'),
    path('send-group-notification/<uuid:group_pk>/', views.send_group_notification, name='send_group'),
    path('resend/<uuid:pk>/', views.resend_notification, name='resend'),
]
