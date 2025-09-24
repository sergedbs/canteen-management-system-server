from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.utils import extract_name_from_email

User = get_user_model()


class TokenWithRoleObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["mfa_enabled"] = user.mfa_enabled

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # If MFA is enabled, don't return tokens immediately
        if user.mfa_enabled:
            return {
                "mfa_required": True,
                "email": user.email,
                "mfa_type": user.mfa_type,
                "message": "MFA verification required",
            }

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "password2")

    def validate_email(self, value):
        if not value.lower().endswith("utm.md"):
            raise serializers.ValidationError("Registration allowed only with *.utm.md email.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value, self.instance)
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        first, last = extract_name_from_email(validated_data["email"])
        validated_data["first_name"] = first
        validated_data["last_name"] = last
        user = User.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        refresh = TokenWithRoleObtainPairSerializer.get_token(instance)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        return data


class MFASetupSerializer(serializers.Serializer):
    mfa_type = serializers.ChoiceField(choices=[("totp", "Authenticator")])


class MFAVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10)  # Support both 6-digit OTP and backup codes


class MFADisableSerializer(serializers.Serializer):
    password = serializers.CharField()
