from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from apps.authentication.utils import get_custom_token
from apps.users.utils import extract_name_from_email

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return get_custom_token(user)


class RefreshSerializer(TokenRefreshSerializer):
    refresh = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        # Get refresh token from cookie
        refresh_token = self.context["request"].COOKIES.get("refresh_token")
        if not refresh_token:
            raise InvalidToken("No valid token found in cookie 'refresh_token'")

        # Set it in attrs for parent validation
        attrs["refresh"] = refresh_token
        return super().validate(attrs)


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
        refresh = get_custom_token(instance)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        return data


class MFAVerifySerializer(serializers.Serializer):
    ticket = serializers.CharField(max_length=64)
    code = serializers.CharField(max_length=10)


class MFADisableSerializer(serializers.Serializer):
    password = serializers.CharField()


class MFASetupStartSerializer(serializers.Serializer):
    pass


class MFASetupConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class EmailResendSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class MFABackupCodesRegenerateSerializer(serializers.Serializer):
    password = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate_new_password(self, value):
        user = self.context["request"].user
        password_validation.validate_password(value, user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_new_password = serializers.CharField(required=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Password fields didn't match."})
        return attrs

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
