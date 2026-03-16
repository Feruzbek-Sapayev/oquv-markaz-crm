from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from .serializers import PaymentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'group', 'status', 'month', 'year']
    ordering_fields = ['paid_at', 'created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
