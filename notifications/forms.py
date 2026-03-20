from django import forms
from accounts.models import CustomUser

class MassNotificationForm(forms.Form):
    RECIPIENT_CHOICES = [
        ('all', 'Barcha foydalanuvchilar'),
        ('teacher', 'Barcha o\'qituvchilar'),
        ('student', 'Barcha o\'quvchilar'),
        ('admin', 'Barcha adminlar'),
        ('specific', 'Tanlangan foydalanuvchilar'),
    ]
    recipient_type = forms.ChoiceField(choices=RECIPIENT_CHOICES, label="Kimga", widget=forms.Select(attrs={'class': 'form-select'}))
    specific_users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        label="Foydalanuvchilarni tanlang",
        widget=forms.SelectMultiple(attrs={'class': 'form-select select2', 'style': 'width: 100%', 'placeholder': 'Foydalanuvchilarni tanlang'})
    )
    title = forms.CharField(max_length=255, label="Sarlavha", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Xabar sarlavhasi'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Xabar matnini kiriting...'}), label="Xabar")
