from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.menus.models import Category, Item, Menu, MenuItem


class ItemInline(TabularInline):
    model = Item
    extra = 0
    autocomplete_fields = ["category"]
    exclude = ("deleted_at",)


class MenuItemInline(TabularInline):
    model = MenuItem
    extra = 0
    autocomplete_fields = ["item"]
    exclude = ("deleted_at",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "display_order")
    search_fields = ("name",)
    exclude = ("deleted_at",)


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ("name", "category", "base_price")
    list_filter = ("category",)
    search_fields = ("name",)
    exclude = ("deleted_at",)


@admin.register(Menu)
class MenuAdmin(ModelAdmin):
    list_display = ("name", "start_time", "end_time", "is_active")
    inlines = [MenuItemInline]
    search_fields = ("name",)
    exclude = ("deleted_at",)


@admin.register(MenuItem)
class MenuItemAdmin(ModelAdmin):
    list_display = ("menu", "item", "display_order")
    list_filter = ("menu", "item")
    search_fields = ("item__name", "menu__name")
    exclude = ("deleted_at",)
