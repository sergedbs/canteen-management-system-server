from rest_framework import permissions as drf_permissions

from .drf_permissions import CustomerVerificationRequired, RoleBasedPermission
from .utils import is_admin_or_staff, is_authenticated


class PermissionMixin:
    permission_classes = [drf_permissions.IsAuthenticated, RoleBasedPermission]

    # Optional
    action_permission_classes = {
        # Example: 'create': [drf_permissions.IsAuthenticated, CustomerVerificationRequired],
        # Example: 'update': [drf_permissions.IsAuthenticated, CustomerVerificationRequired],
    }

    def get_permissions(self):
        action = getattr(self, "action", None)

        # Check if we have specific permissions for this action
        if action and action in self.action_permission_classes:
            permission_classes = self.action_permission_classes[action]
        else:
            permission_classes = self.permission_classes

        return [perm() for perm in permission_classes]


class OwnershipMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        user = getattr(self.request, "user", None)

        # Anonymous or unauthenticated users get nothing
        if not user or not is_authenticated(user):
            return queryset.none()

        # Admin/staff see everything
        if is_admin_or_staff(user):
            return queryset

        # Regular users see only their own objects
        model = getattr(queryset, "model", None)
        if model:
            if hasattr(model, "user"):
                return queryset.filter(user=user)

            if hasattr(model, "owner"):
                return queryset.filter(owner=user)

        return queryset.none()


class CustomerVerificationMixin:
    def get_permissions(self):
        permissions = super().get_permissions() if hasattr(super(), "get_permissions") else []

        action = getattr(self, "action", None)
        if action in ["create", "update", "partial_update", "destroy"]:
            permissions.append(CustomerVerificationRequired())

        return permissions
