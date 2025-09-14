from rest_framework import serializers

from apps.menus.models import Item, Menu, MenuItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "base_price"]


class MenuItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "quantity", "item"]


class MenuSerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = ["id", "name", "start_time", "end_time", "menu_items"]
