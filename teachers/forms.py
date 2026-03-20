from django import forms
from django.contrib.auth.hashers import make_password
from .models import Teacher
from accounts.models import CustomUser


class TeacherForm(forms.ModelForm):
    username = forms.CharField(label="Foydalanuvchi nomi", max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: jasur_teacher'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}), required=False)

    class Meta:
        model = Teacher
        fields = [
            'last_name', 'first_name', 'middle_name', 'phone', 'email',
            'gender', 'birth_date', 'address', 'photo', 'status',
            'hired_at', 'notes'
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiya'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Otasining ismi'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.uz'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Yashash manzili...'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'hired_at': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
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
        teacher = super().save(commit=False)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not teacher.user and username and password:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                first_name=teacher.first_name,
                last_name=teacher.last_name,
                role=CustomUser.Role.TEACHER,
                phone=teacher.phone
            )
            teacher.user = user
        elif teacher.user:
            # Sync info and update password if provided
            user = teacher.user
            user.username = username
            user.first_name = teacher.first_name
            user.last_name = teacher.last_name
            user.phone = teacher.phone
            if password:
                user.set_password(password)
            user.save()

        if commit:
            teacher.save()
        return teacher
