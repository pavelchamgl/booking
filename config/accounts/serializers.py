import re

from rest_framework import serializers

from .models import CustomUser
from .utils import create_and_send_otp


class PasswordValidateMixin(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"error": "Password fields didn't match."})

        password = attrs['password']
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({'password': "Password must contain at least one uppercase letter."})
        if not re.search(r'[!@#$%^&*]', password):
            raise serializers.ValidationError(
                {'password': "Password must contain at least one special character (!@#$%^&*)."})
        if len(password) < 8:
            raise serializers.ValidationError({'password': "Password must be at least 8 characters long."})
        return attrs


class UserRegisterSerializer(serializers.ModelSerializer, PasswordValidateMixin):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password',
            'confirm_password',
        ]

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(**validated_data)
        if user:
            create_and_send_otp(user, "EmailConfirmation")
            return user
        return None


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class EmailConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
