from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Student
from .serializers import StudentSerializer, StudentListSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'gender']
    search_fields = ['first_name', 'last_name', 'phone']
    ordering_fields = ['first_name', 'last_name', 'registered_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentSerializer
