from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.session_list, name='session_list'),
    path('update-ajax/', views.attendance_update_ajax, name='attendance_update_ajax'),
    path('grade-update-ajax/', views.grade_update_ajax, name='grade_update_ajax'),
    path('update-topic/', views.update_topic_ajax, name='update_topic_ajax'),
    path('export-excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('export-grades-excel/', views.export_grades_excel, name='export_grades_excel'),
    path('groups/<uuid:group_pk>/create/', views.session_create, name='session_create'),
    path('<uuid:pk>/', views.session_detail, name='session_detail'),
    path('<uuid:pk>/delete/', views.session_delete, name='session_delete'),
]
