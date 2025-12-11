from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.webhooks.models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(ModelAdmin):
    list_display = ["event_id", "event_type", "source", "status", "created_at"]
    list_filter = ["source", "status", "event_type"]
    search_fields = ["event_id", "event_type"]
    readonly_fields = ["event_id", "event_type", "source", "payload", "created_at", "updated_at"]
    ordering = ["-created_at"]
