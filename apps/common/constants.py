from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    PAID = "paid", "Paid"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
