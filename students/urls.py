from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('<uuid:pk>/', views.student_detail, name='detail'),
    path('create/', views.student_create, name='create'),
    path('<uuid:pk>/edit/', views.student_edit, name='edit'),
    path('<uuid:pk>/delete/', views.student_delete, name='delete'),
    path('export/excel/', views.student_export_excel, name='export_excel'),
    path('<uuid:student_id>/add-exam/', views.add_exam, name='add_exam'),
]
