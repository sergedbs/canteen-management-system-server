from django.db.models import Sum
from rest_framework import serializers

from apps.menus.models import Menu, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name")
    item_description = serializers.CharField(source="item.description")
    item_base_price = serializers.DecimalField(source="item.base_price", max_digits=10, decimal_places=2)
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "quantity", "item_name", "item_description", "item_base_price", "remaining_quantity"]

    def get_remaining_quantity(self, obj):
        ordered_quantity = (
            obj.order_items.filter(order__status__in=["pending", "confirmed"]).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        return obj.quantity - ordered_quantity


class MenuSerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = ["id", "name", "start_time", "end_time", "menu_items", "type"]
