from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Group, Enrollment, Exam
from .serializers import (
    CourseSerializer, GroupSerializer, GroupListSerializer, 
    EnrollmentSerializer, ExamSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'teacher', 'days', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'start_date', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return GroupListSerializer
        return GroupSerializer

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'group', 'is_active']

class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['student', 'group']
    search_fields = ['title']
