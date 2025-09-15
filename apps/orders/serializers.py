import random
import string
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from apps.common.constants import OrderStatus
from apps.menus.models import Menu, MenuItem
from apps.orders.models import Order, OrderItem


class OrderItemCreateSerializer(serializers.Serializer):
    menu_item_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source="menu_item")
    quantity = serializers.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        menu = self.context.get("menu")
        if menu:
            self.fields["menu_item_id"].queryset = MenuItem.objects.filter(menu=menu)

    def validate(self, attrs):
        menu_item = attrs["menu_item"]
        qty = attrs["quantity"]

        reserved = (
            OrderItem.objects.filter(menu_item=menu_item, order__status__in=OrderStatus.active())
            .aggregate(total=Sum("quantity"))
            .get("total")
            or 0
        )

        remaining = menu_item.quantity - reserved

        if qty > remaining:
            raise serializers.ValidationError(f"Only {remaining} pcs. available for {menu_item.item.name}.")
        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    order_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "menu",
            "reservation_time",
            "items",
            "order_no",
            "status",
            "total_amount",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and hasattr(self, "initial_data"):
            menu_id = self.initial_data.get("menu")
            if menu_id:
                try:
                    menu = Menu.objects.get(pk=menu_id)
                    self.fields["items"].child.context.update({"menu": menu})
                except Menu.DoesNotExist:
                    pass

    @staticmethod
    def _generate_order_no():
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=6))
            if not Order.objects.filter(order_no=code).exists():
                return code.upper()

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user

        order = Order.objects.create(
            user=user,
            order_no=self._generate_order_no(),
            total_amount=Decimal("0.00"),
            **validated_data,
        )

        total_amount = Decimal("0.00")
        for item_data in items_data:
            menu_item = item_data["menu_item"]
            qty = item_data["quantity"]

            unit_price = menu_item.override_price or menu_item.item.base_price
            total_price = unit_price * qty

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price,
            )

            total_amount += total_price

        order.total_amount = total_amount
        order.save()

        return order
