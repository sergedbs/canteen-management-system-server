from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.orders.models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu_item", "quantity", "unit_price", "total_price")
    exclude = ("deleted_at",)
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_no", "user", "menu", "status", "total_amount", "reservation_time", "created_at")
    list_filter = ("status", "menu", "created_at", "reservation_time")
    search_fields = ("order_no", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("order_no", "total_amount", "created_at", "updated_at")
    exclude = ("deleted_at",)
    inlines = [OrderItemInline]
    autocomplete_fields = ["user", "menu"]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.has_perm("orders.change_order_status"):
            readonly.append("status")
        return readonly

    def get_list_display_links(self, request, list_display):
        return ("order_no",)


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ("order_no", "menu_item_name", "quantity", "unit_price", "total_price")
    list_filter = ("order__status", "menu_item__item__category")
    search_fields = ("order__order_no", "menu_item__item__name")
    readonly_fields = ("created_at", "updated_at")
    exclude = ("deleted_at",)
    autocomplete_fields = ["order", "menu_item"]

    def order_no(self, obj):
        return obj.order.order_no

    order_no.short_description = "Order No"
    order_no.admin_order_field = "order__order_no"

    def menu_item_name(self, obj):
        return obj.menu_item.item.name

    menu_item_name.short_description = "Item"
    menu_item_name.admin_order_field = "menu_item__item__name"
