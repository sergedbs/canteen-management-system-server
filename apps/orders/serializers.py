import random
import string
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
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

    def validate(self, attrs):
        items = self.initial_data.get("items", [])
        total_amount = Decimal("0.00")

        menu = attrs.get("menu")
        reservation_time = attrs.get("reservation_time")
        if not menu:
            raise serializers.ValidationError({"menu": "Menu must be specified."})

        if menu.start_time <= timezone.now():
            raise serializers.ValidationError({"menu": "Cannot create orders for menus that have already started."})

        if not (menu.start_time <= reservation_time <= menu.end_time):
            raise serializers.ValidationError(
                {"reservation_time": "Reservation time must be between the menu's start and end times."}
            )

        for item in items:
            try:
                menu_item = MenuItem.objects.get(pk=item["menu_item_id"])
            except MenuItem.DoesNotExist as e:
                raise serializers.ValidationError({"items": f"Menu item {item['menu_item_id']} does not exist"}) from e

            if menu_item.menu_id != menu.id:
                raise serializers.ValidationError(
                    {"items": f"Menu item {menu_item.item.name} does not belong to menu {menu.name}."}
                )

            qty = int(item["quantity"])
            unit_price = menu_item.override_price or menu_item.item.base_price
            total_amount += unit_price * qty

        user = self.context["request"].user
        balance = user.balance

        available = balance.current_balance - balance.on_hold
        if total_amount > available:
            raise serializers.ValidationError(
                {"balance": f"Insufficient funds. Order total is {total_amount}, but only {available} is available."}
            )

        return attrs

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
        user.balance.on_hold += total_amount
        user.balance.save()

        return order


class OrderItemListSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="menu_item.item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["item_name", "quantity"]


class OrderListSerializer(serializers.ModelSerializer):
    menu = serializers.CharField(source="menu.name", read_only=True)
    items = OrderItemListSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "menu",
            "items",
            "is_active",
            "order_no",
            "status",
            "total_amount",
            "reservation_time",
            "user",
        ]

    def get_is_active(self, obj):
        return obj.menu.end_time > timezone.now()
