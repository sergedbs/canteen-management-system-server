from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Session


@admin.register(Session)
class SessionAdmin(ModelAdmin):
    list_display = (
        "user",
        "sid",
        "ip_address",
        "user_agent",
        "device_label",
        "created_at",
        "last_seen_at",
        "expires_at",
        "is_revoked",
        "mfa_passed",
    )
    list_filter = ("user",)
    search_fields = ("user",)
