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
    
    @classmethod
    def active(cls):
        return [cls.PENDING, cls.PREPARING, cls.PAID, cls.COMPLETED]

class TransactionType(models.TextChoices):
    DEPOSIT = "deposit", "Deposit"
    PAYMENT = "payment", "Payment"
    REFUND = "refund", "Refund"
    
    
class MenuType(models.TextChoices):
    BREAKFAST = "breakfast", "Breakfast"
    LUNCH = "lunch", "Lunch"
    DINNER = "dinner", "Dinner"


ROLE_GROUP_NAMES = ["admin", "staff", "customer_verified", "customer_unverified"]


