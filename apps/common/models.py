import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        if self.is_active:
            self.is_active = False
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_active", "updated_at", "deleted_at"])

    def restore(self):
        if not self.is_active:
            self.is_active = True
            self.deleted_at = None
            self.save(update_fields=["is_active", "updated_at", "deleted_at"])
