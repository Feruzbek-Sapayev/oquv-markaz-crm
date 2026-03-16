from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from teachers.models import Teacher
from students.models import Student


class CustomUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'avatar', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    teacher_profile = forms.ModelChoiceField(
        queryset=Teacher.objects.filter(user__isnull=True),
        required=False,
        label="O'qituvchi profili",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    student_profile = forms.ModelChoiceField(
        queryset=Student.objects.filter(user__isnull=True),
        required=False,
        label="O'quvchi profili",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        if self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            
            # If editing, include current profile and those without users
            if self.instance.role == 'teacher':
                current_p = getattr(self.instance, 'teacher_profile', None)
                qs = Teacher.objects.filter(models.Q(user__isnull=True) | models.Q(pk=current_p.pk if current_p else None))
                self.fields['teacher_profile'].queryset = qs
                if current_p:
                    self.fields['teacher_profile'].initial = current_p
            elif self.instance.role == 'student':
                current_p = getattr(self.instance, 'student_profile', None)
                qs = Student.objects.filter(models.Q(user__isnull=True) | models.Q(pk=current_p.pk if current_p else None))
                self.fields['student_profile'].queryset = qs
                if current_p:
                    self.fields['student_profile'].initial = current_p

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
