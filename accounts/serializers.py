from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'role_display', 'phone', 'avatar_url'
        )
        read_only_fields = ('id', 'role_display', 'full_name', 'avatar_url')

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'first_name', 'last_name', 'email', 'role', 'phone')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user
