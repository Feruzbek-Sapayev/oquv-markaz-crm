from django import forms
from django.contrib.auth.hashers import make_password
from .models import Student
from accounts.models import CustomUser


class StudentForm(forms.ModelForm):
    username = forms.CharField(label="Foydalanuvchi nomi", max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: ali_dev'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}), required=False)

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'middle_name', 'phone', 'parent_phone',
            'gender', 'birth_date', 'address', 'photo', 'status', 
            'telegram_id', 'telegram_notifications', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiya'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Otasining ismi'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 987 65 43'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Yashash manzili...'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'telegram_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 123456789'}),
            'telegram_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Qo\'shimcha izohlar...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['username'].required = True
            self.fields['password'].required = True
        else:
            self.fields['username'].initial = self.instance.user.username if self.instance.user else ''
            self.fields['username'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username is taken by any other user
        qs = CustomUser.objects.filter(username=username)
        if self.instance.pk and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)
            
        if qs.exists():
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
            user.username = username
            user.first_name = student.first_name
            user.last_name = student.last_name
            user.phone = student.phone
            if password:
                user.set_password(password)
            user.save()

        if commit:
            student.save()
        return student
