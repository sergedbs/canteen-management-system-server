from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    STAFF = "staff", "Staff"
    ADMIN = "admin", "Administrator"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    PAID = "paid", "Paid"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class TransactionType(models.TextChoices):
    DEPOSIT = "deposit", "Deposit"
    PAYMENT = "payment", "Payment"
    REFUND = "refund", "Refund"


ROLE_GROUP_NAMES = ["admin", "staff", "customer_verified", "customer_unverified"]
