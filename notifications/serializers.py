from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('recipient', 'sender', 'is_read')
