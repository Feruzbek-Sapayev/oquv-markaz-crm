from rest_framework import serializers
from .models import Course, Group, Enrollment, Exam
from teachers.serializers import TeacherListSerializer

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'

class GroupListSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_detail = TeacherListSerializer(source='teacher', read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = (
            'id', 'name', 'course_name', 'teacher_detail', 'start_time', 
            'end_time', 'days', 'student_count', 'is_active'
        )

class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    discounted_fee = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = Exam
        fields = '__all__'
