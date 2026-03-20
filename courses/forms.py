from django import forms
from .models import Course, Room, Group, Enrollment, Exam, GroupDiscount
from teachers.models import Teacher


UZ_MONTHS = {
    1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
    5: 'May', 6: 'Iyun', 7: 'Iyul', 8: 'Avgust',
    10: 'Oktabr', 9: 'Sentabr', 11: 'Noyabr', 12: 'Dekabr'
}


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['image', 'name', 'description', 'duration_months', 'monthly_fee', 'is_active']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kurs nomi, masalan: Python Backend'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Kurs haqida qisqacha ma\'lumot...'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Davomiyligi (oy)'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Oylik to\'lov'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Xona nomi, masalan: A-101'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sig\'imi'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Xona haqida ma\'lumot...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = [
            'name', 'course', 'teacher', 'start_time', 'end_time', 'days', 
            'start_date', 'end_date', 'max_students', 'room', 'is_active',
            'salary_type', 'salary_monthly', 'salary_percentage'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guruh nomi, masalan: P1-2024'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'days': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maksimal o\'quvchilar soni'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'salary_type': forms.Select(attrs={'class': 'form-select'}),
            'salary_monthly': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Belgilangan oylik'}),
            'salary_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Foizda (%)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(status='active').order_by('last_name', 'first_name')



class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'enrolled_at', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'enrolled_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Izoh...'}),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        from students.models import Student
        students = Student.objects.filter(status='active')
        if group is not None:
            enrolled_ids = group.enrollments.values_list('student_id', flat=True)
            students = students.exclude(id__in=enrolled_ids)
        self.fields['student'].queryset = students.order_by('last_name')

class EnrollmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Izoh...'}),
        }

class GroupDiscountForm(forms.ModelForm):
    month_year = forms.ChoiceField(label='Tanlangan oy', widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = GroupDiscount
        fields = ['enrollment', 'discount_type', 'percent', 'amount', 'notes']
        widgets = {
            'enrollment': forms.Select(attrs={'class': 'form-select'}),
            'discount_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_discount_type'}),
            'percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Foizda (%)'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Summada (so\'m)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': "Izoh..."}),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        
        # Filter: only active and from current group if provided
        qs = Enrollment.objects.filter(is_active=True).select_related('student', 'group')
        if group:
            qs = qs.filter(group=group)
            
        self.fields['enrollment'].queryset = qs
        self.fields['enrollment'].widget.attrs.update({'class': 'form-select'})
        
        # Populate month_year choices if group provided
        if group:
            import datetime
            choices = []
            curr = datetime.date(group.start_date.year, group.start_date.month, 1)
            for _ in range(group.course.duration_months):
                label = f"{UZ_MONTHS.get(curr.month, curr.month)} {curr.year}"
                choices.append((f"{curr.month}-{curr.year}", label))
                if curr.month == 12: curr = datetime.date(curr.year + 1, 1, 1)
                else: curr = datetime.date(curr.year, curr.month + 1, 1)
            self.fields['month_year'].choices = choices

    def clean_enrollment(self):
        enrollment = self.cleaned_data.get('enrollment')
        if enrollment and not enrollment.is_active:
            raise forms.ValidationError("Faqat faol o'quvchilarga chegirma berish mumkin!")
        return enrollment

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['student', 'group', 'title', 'score', 'max_score', 'date']
        widgets = {
            'student': forms.HiddenInput(),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: Final Exam yoki Quarter 1'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'To\'plangan ball'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maksimal ball'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.get('initial', {}).get('student')
        super().__init__(*args, **kwargs)
        if student:
            self.fields['group'].queryset = Group.objects.filter(enrollments__student=student, enrollments__is_active=True).distinct()
