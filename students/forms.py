from django import forms
from django.contrib.auth.hashers import make_password
from .models import Student
from accounts.models import CustomUser


class StudentForm(forms.ModelForm):
    username = forms.CharField(label="Foydalanuvchi nomi", max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'middle_name', 'phone', 'parent_phone',
            'gender', 'birth_date', 'address', 'photo', 'status', 
            'telegram_id', 'telegram_notifications', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'telegram_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 123456789'}),
            'telegram_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['username'].required = True
            self.fields['password'].required = True
        else:
            self.fields['username'].initial = self.instance.user.username if self.instance.user else ''
            self.fields['username'].disabled = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.instance.pk:
            if CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError("Ushbu foydalanuvchi nomi band!")
        return username

    def save(self, commit=True):
        student = super().save(commit=False)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not student.user and username and password:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                first_name=student.first_name,
                last_name=student.last_name,
                role=CustomUser.Role.STUDENT,
                phone=student.phone
            )
            student.user = user
        elif student.user:
            # Sync info and update password if provided
            user = student.user
            user.first_name = student.first_name
            user.last_name = student.last_name
            user.phone = student.phone
            if password:
                user.set_password(password)
            user.save()

        if commit:
            student.save()
        return student
