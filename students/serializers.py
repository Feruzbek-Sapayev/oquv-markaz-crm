from rest_framework import serializers
from .models import Student

class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    lead_status_data = serializers.JSONField(source='lead_status', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

class StudentListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Student
        fields = ('id', 'first_name', 'last_name', 'full_name', 'phone', 'photo', 'status')
