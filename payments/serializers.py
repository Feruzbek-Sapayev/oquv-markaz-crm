from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('status', 'status_display', 'remaining')
