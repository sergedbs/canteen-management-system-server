from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        db_table = "category"
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name


class Item(BaseModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="items",
        db_column="category_id",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        db_table = "item"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["name"]),
        ]
        unique_together = [("category", "name")]

    def __str__(self):
        return self.name


class Menu(BaseModel):
    name = models.CharField(max_length=120)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        db_table = "menu"
        indexes = [
            models.Index(fields=["start_time"]),
            models.Index(fields=["end_time"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class MenuItem(BaseModel):
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="menu_items",
        db_column="menu_id",
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="menu_items", db_column="item_id")
    display_order = models.IntegerField(default=0)
    quantity = models.PositiveIntegerField()
    override_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_permanent = models.BooleanField(default=False)

    class Meta:
        db_table = "menu_item"
        unique_together = [("menu", "item")]
        indexes = [
            models.Index(fields=["menu", "display_order"]),
            models.Index(fields=["item"]),
        ]
        ordering = ["menu", "display_order"]

    def __str__(self):
        return f"{self.menu} · {self.item}"
