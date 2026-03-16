from rest_framework import serializers
from .models import AttendanceSession, Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'

class AttendanceSessionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    records = AttendanceSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceSession
        fields = '__all__'
