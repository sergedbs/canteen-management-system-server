from django.contrib import admin

from apps.menus.models import Category, Item, Menu, MenuItem


class ItemInline(admin.TabularInline):  # or StackedInline if you want a bigger form
    model = Item
    extra = 1  # show 1 empty form by default
    autocomplete_fields = ["category"]  # easy selection of categories


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    autocomplete_fields = ["item"]  # so you can select from existing items


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order")
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "base_price")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "is_active")
    inlines = [MenuItemInline]  # attach MenuItems directly
    search_fields = ("name",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("menu", "item", "display_order")
    list_filter = ("menu", "item")
    search_fields = ("item__name", "menu__name")
