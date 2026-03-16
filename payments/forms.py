from django import forms
from .models import Payment
from students.models import Student
from courses.models import Group


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'group', 'amount', 'method', 'month', 'year', 'paid_at', 'due_date', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020}),
            'paid_at': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(status='active').order_by('last_name')
        self.fields['group'].queryset = Group.objects.filter(is_active=True).select_related('course')
