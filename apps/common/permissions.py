from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from rest_framework.permissions import BasePermission

ROLE_PERMISSIONS = {
    "admin": [
        # At the moment the Admin has all the permissions
        # This can be changed later, if someone needs to be restricted
    ],
    "staff": [
        # Staff is going to have privileges in the following areas(apps):
        # 1. Menus App (Category, Item, Menu, MenuItem)
        ("menus", "add_menu"),
        ("menus", "change_menu"),
        ("menus", "view_menu"),
        ("menus", "delete_menu"),
        ("menus", "add_category"),
        ("menus", "change_category"),
        ("menus", "view_category"),
        ("menus", "delete_category"),
        ("menus", "add_item"),
        ("menus", "change_item"),
        ("menus", "view_item"),
        ("menus", "delete_item"),
        ("menus", "add_menuitem"),
        ("menus", "change_menuitem"),
        ("menus", "view_menuitem"),
        ("menus", "delete_menuitem"),
        ("menus", "change_menuitem_price"),
        ("menus", "change_menuitem_quantity"),
        ("menus", "set_menuitem_permanent"),
        # 2. Orders App
        ("orders", "view_order"),
        ("orders", "change_order_status"),
        ("orders", "view_all_orders"),
        ("orders", "add_orderitem"),
        ("orders", "change_orderitem"),
        ("orders", "view_orderitem"),
        ("orders", "delete_orderitem"),
        # 3. Wallets App (Balance, Transaction)
        ("wallets", "add_balance"),
        ("wallets", "change_balance"),
        ("wallets", "view_balance"),
        ("wallets", "delete_balance"),
        ("wallets", "credit_balance"),
        ("wallets", "debit_balance"),
        ("wallets", "add_transaction"),
        ("wallets", "change_transaction"),
        ("wallets", "view_transaction"),
        ("wallets", "delete_transaction"),
        ("wallets", "refund_payment"),
        ("wallets", "view_all_transactions"),
    ],
    "customer_verified": [
        # The verified customer will have privileges regarding the following areas:
        # 1. Menus App - view only
        ("menus", "view_menu"),
        ("menus", "view_category"),
        ("menus", "view_item"),
        ("menus", "view_menuitem"),
        # 2. Orders App - can create and view their own orders
        ("orders", "add_order"),
        ("orders", "change_order"),
        ("orders", "view_order"),
        ("orders", "delete_order"),
        ("orders", "add_orderitem"),
        ("orders", "change_orderitem"),
        ("orders", "view_orderitem"),
        ("orders", "delete_orderitem"),
        # 3. Wallets App - can view their own balance and transactions
        ("wallets", "view_balance"),
        ("wallets", "view_transaction"),
    ],
    "customer_unverified": [
        # The unverified customer has very limited privileges
        ("menus", "view_menu"),
        ("menus", "view_category"),
        ("menus", "view_item"),
        ("menus", "view_menuitem"),
    ],
}


def _get_permission(app_label: str, codename: str):
    try:
        return Permission.objects.get(content_type__app_label=app_label, codename=codename)
    except Permission.DoesNotExist:
        print(f"WARNING: Permission {app_label}.{codename} does not exist!")
        return None


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    for role, perm_list in ROLE_PERMISSIONS.items():
        group, created = Group.objects.get_or_create(name=role)

        if role == "admin":
            all_perms = Permission.objects.all()
            group.permissions.set(all_perms)
        else:
            perms = list(filter(None, (_get_permission(app, code) for app, code in perm_list)))
            if not perms:
                print(f"WARNING: No permissions found for role '{role}'!")
            group.permissions.set(perms)

        if created:
            print(f"Created group '{role}' with permissions")
        else:
            print(f"Updated group '{role}' with permissions")


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

