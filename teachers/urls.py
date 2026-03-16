from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('create/', views.teacher_create, name='create'),
    path('<uuid:pk>/', views.teacher_detail, name='detail'),
    path('<uuid:pk>/edit/', views.teacher_edit, name='edit'),
    path('<uuid:pk>/delete/', views.teacher_delete, name='delete'),
]
