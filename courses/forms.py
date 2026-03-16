from django import forms
from .models import Course, Group, Enrollment, Exam
from teachers.models import Teacher


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['image', 'name', 'description', 'duration_months', 'monthly_fee', 'is_active']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control'}),
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
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'days': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'salary_type': forms.Select(attrs={'class': 'form-select'}),
            'salary_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(status='active').order_by('last_name', 'first_name')



class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'discount_percent', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
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

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['student', 'group', 'title', 'score', 'max_score', 'date']
        widgets = {
            'student': forms.HiddenInput(),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: Unit 1 Test'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.get('initial', {}).get('student')
        super().__init__(*args, **kwargs)
        if student:
            self.fields['group'].queryset = Group.objects.filter(enrollments__student=student, enrollments__is_active=True).distinct()
