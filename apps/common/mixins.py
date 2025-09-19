from .drf_permissions import CustomerVerificationRequired, IsOwnerOrAdmin, RoleBasedPermission
from .utils import is_admin_or_staff, is_authenticated


class PermissionMixin:
    permission_classes = [RoleBasedPermission]


class OwnershipMixin:
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = getattr(self.request, "user", None)

        if not user or not is_authenticated(user):
            return queryset.none()

        if is_admin_or_staff(user):
            return queryset

        model = getattr(queryset, "model", None)
        if model:
            if hasattr(model, "user"):
                return queryset.filter(user=user)
            if hasattr(model, "owner"):
                return queryset.filter(owner=user)

        return queryset.none()


class VerifiedCustomerMixin:
    permission_classes = [CustomerVerificationRequired]


class VerifiedOwnerMixin:
    permission_classes = [CustomerVerificationRequired, IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = getattr(self.request, "user", None)

        if not user or not is_authenticated(user):
            return queryset.none()

        if is_admin_or_staff(user):
            return queryset

        model = getattr(queryset, "model", None)
        if model:
            if hasattr(model, "user"):
                return queryset.filter(user=user)
            if hasattr(model, "owner"):
                return queryset.filter(owner=user)

        return queryset.none()


# Examples of how to use the mixins:
# class MenuListView(PermissionMixin, ListAPIView):
#     required_permission = "menus.view_menu"
#     # Unverified customers can see if they have this permission

# class OrderDetailView(OwnershipMixin, RetrieveAPIView):
#     # Checks object permissions for individual orders
#     pass

# class UserOrdersView(OwnershipMixin, ListAPIView):
#     # Filters queryset + checks object permissions
#     pass

# class MenuManagementView(PermissionMixin, ListAPIView):
#     required_permission = "menus.add_menu"
#     # Staff with permission can manage menus
#     pass
