from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('create/', views.payment_create, name='create'),
    path('<uuid:pk>/edit/', views.payment_edit, name='edit'),
    path('<uuid:pk>/delete/', views.payment_delete, name='delete'),
    path('<uuid:pk>/pdf/', views.payment_pdf, name='pdf'),
    path('debtors/', views.debtor_list, name='debtors'),
    path('export/excel/', views.payment_export_excel, name='export_excel'),
]
