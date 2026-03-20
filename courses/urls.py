from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('', views.course_list, name='course_list'),
    path('<uuid:pk>/', views.course_detail, name='course_detail'),
    path('create/', views.course_create, name='course_create'),
    path('<uuid:pk>/edit/', views.course_edit, name='course_edit'),
    path('<uuid:pk>/delete/', views.course_delete, name='course_delete'),
    # Rooms
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<uuid:pk>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<uuid:pk>/delete/', views.room_delete, name='room_delete'),
    # Groups
    path('groups/', views.group_list, name='group_list'),
    path('groups/<uuid:pk>/', views.group_detail, name='group_detail'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<uuid:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<uuid:pk>/delete/', views.group_delete, name='group_delete'),
    path('groups/<uuid:pk>/export/', views.group_export_excel, name='group_export'),
    path('schedule/', views.lesson_schedule, name='lesson_schedule'),
    # Enrollments
    path('groups/<uuid:group_pk>/enroll/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<uuid:pk>/edit/', views.enrollment_edit, name='enrollment_edit'),
    path('enrollments/<uuid:pk>/remove/', views.enrollment_remove, name='enrollment_remove'),
    path('discount/create/', views.discount_create, name='discount_create'),
    path('discount/<uuid:pk>/delete/', views.discount_delete, name='discount_delete'),
]
