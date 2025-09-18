from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from apps.wallets.models import Balance, Transaction


class TransactionInline(TabularInline):
    model = Transaction
    extra = 0
    exclude = ("deleted_at",)
    ordering = ("-created_at",)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.has_perm("wallets.change_transaction"):
            return ("signed_amount", "created_at")
        return ("type", "signed_amount", "remaining_balance", "order", "created_at")

    def get_can_delete(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm("wallets.delete_transaction")

    def signed_amount(self, obj):
        if obj.type == "payment":
            return format_html('<span style="color: red;">-{}</span>', obj.amount)
        elif obj.type == "deposit":
            return format_html('<span style="color: green;">+{}</span>', obj.amount)
        elif obj.type == "refund":
            return format_html('<span style="color: blue;">+{}</span>', obj.amount)
        return obj.amount

    signed_amount.short_description = "Amount"

    def has_add_permission(self, request, obj):
        return request.user.is_superuser or request.user.has_perm("wallets.add_transaction")


@admin.register(Balance)
class BalanceAdmin(ModelAdmin):
    list_display = ("user", "current_balance_colored", "on_hold", "available_balance", "created_at")
    list_filter = ("created_at", "user__groups")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("available_balance", "created_at", "updated_at")
    exclude = ("deleted_at",)
    inlines = [TransactionInline]
    autocomplete_fields = ["user"]

    def current_balance_colored(self, obj):
        color = "green" if obj.current_balance > 0 else "red" if obj.current_balance < 0 else "black"
        return format_html('<span style="color: {};">{}</span>', color, obj.current_balance)

    current_balance_colored.short_description = "Current Balance"
    current_balance_colored.admin_order_field = "current_balance"

    def available_balance(self, obj):
        return obj.current_balance - obj.on_hold

    available_balance.short_description = "Available Balance"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not (request.user.is_superuser or request.user.has_perm("wallets.change_balance")):
            readonly.extend(["current_balance", "on_hold"])
        return readonly

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.has_perm("wallets.add_balance")

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm("wallets.delete_balance")


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ("balance_user", "type_colored", "signed_amount", "remaining_balance", "order_no", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("balance__user__email", "balance__user__first_name", "balance__user__last_name", "order__order_no")
    readonly_fields = ("created_at", "updated_at")
    exclude = ("deleted_at",)
    autocomplete_fields = ["balance", "order"]
    date_hierarchy = "created_at"

    def balance_user(self, obj):
        return obj.balance.user

    balance_user.short_description = "User"
    balance_user.admin_order_field = "balance__user"

    def type_colored(self, obj):
        colors = {"deposit": "green", "payment": "red", "refund": "blue"}
        color = colors.get(obj.type, "black")
        return format_html('<span style="color: {};">{}</span>', color, obj.type.title())

    type_colored.short_description = "Type"
    type_colored.admin_order_field = "type"

    def signed_amount(self, obj):
        if obj.type == "payment":
            return format_html('<span style="color: red;">-{}</span>', obj.amount)
        elif obj.type in ["deposit", "refund"]:
            return format_html('<span style="color: green;">+{}</span>', obj.amount)
        return obj.amount

    signed_amount.short_description = "Amount"
    signed_amount.admin_order_field = "amount"

    def order_no(self, obj):
        return obj.order.order_no if obj.order else "-"

    order_no.short_description = "Order No"
    order_no.admin_order_field = "order__order_no"

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.has_perm("wallets.add_transaction")

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm("wallets.change_transaction")

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm("wallets.delete_transaction")

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or request.user.has_perm("wallets.change_transaction"):
            return ["created_at", "updated_at"]
        return [field.name for field in self.model._meta.fields] + ["created_at", "updated_at"]
