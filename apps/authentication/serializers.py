from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

from apps.users.utils import extract_name_from_email

User = get_user_model()


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
