from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Group, PermissionsMixin
from django.db import models

from apps.common.constants import ROLE_GROUP_NAMES, UserRole
from apps.common.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CUSTOMER)
    is_verified = models.BooleanField(default=True)

    mfa_enabled = models.BooleanField(default=False)
    mfa_type = models.CharField(
        max_length=20, choices=[("email", "Email"), ("totp", "Authenticator")], blank=True, null=True
    )
    mfa_secret = models.CharField(max_length=64, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_role = None
        old_verified = None

        if not is_new:
            try:
                old_user = User.objects.only("role", "is_verified").get(pk=self.pk)
                old_role = old_user.role
                old_verified = old_user.is_verified
            except User.DoesNotExist:
                old_role = None
                old_verified = None
        else:
            old_role = None
            old_verified = None

        super().save(*args, **kwargs)

        if is_new or old_role != self.role or old_verified != self.is_verified:
            try:
                self.assign_group_by_role()
            except (Group.DoesNotExist, ValueError) as e:
                print(f"Warning: Could not assign groups for user {self.email}: {e}")

    def assign_group_by_role(self):
        role_group_names = ROLE_GROUP_NAMES

        role_groups = Group.objects.filter(name__in=role_group_names)
        if role_groups.exists():
            self.groups.remove(*role_groups)

        group_name = self.get_group_name()
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                self.groups.add(group)
            except Group.DoesNotExist:
                print(f"Warning: Group '{group_name}' does not exist for user {self.email}")

    def is_verified_customer(self):
        return self.role == UserRole.CUSTOMER and self.is_verified

    def get_group_name(self):
        if self.role == UserRole.ADMIN:
            return "admin"
        elif self.role == UserRole.STAFF:
            return "staff"
        elif self.role == UserRole.CUSTOMER:
            return "customer_verified" if self.is_verified else "customer_unverified"
        return None

    def is_in_role_group(self, group_name):
        return self.groups.filter(name=group_name).exists()

    def get_role_groups(self):
        return self.groups.filter(name__in=ROLE_GROUP_NAMES)

    def __str__(self):
        verification_status = " (verified)" if self.is_verified and self.role == UserRole.CUSTOMER else ""
        return f"{self.email}{verification_status}"
