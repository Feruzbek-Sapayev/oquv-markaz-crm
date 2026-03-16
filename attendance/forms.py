from django import forms
from .models import AttendanceSession, Attendance


class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['group', 'date', 'topic']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
        }


AttendanceFormSet = forms.modelformset_factory(
    Attendance,
    fields=['status', 'notes'],
    extra=0,
    widgets={
        'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        'notes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
    }
)
