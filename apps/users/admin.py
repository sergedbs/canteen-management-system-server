from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "is_staff", "role", "is_verified")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    filter_horizontal = ("groups",)
    exclude = ("user_permissions",)
    readonly_fields = ("last_login", "all_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Role & Verification", {"fields": ("role", "is_verified")}),
        ("Important dates", {"fields": ("last_login",)}),
        ("Effective permissions (read-only)", {"fields": ("all_permissions",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
    )

    def all_permissions(self, obj):
        if not obj.pk:
            return "—"
        perms = sorted(obj.get_all_permissions())
        return mark_safe("<br>".join(perms))

    all_permissions.short_description = "Effective permissions"
