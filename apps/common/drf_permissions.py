from rest_framework import permissions

from .utils import is_admin_or_staff, is_authenticated, is_customer, is_verified_customer


class IsOwnerOrAdmin(permissions.BasePermission):
    message = "You can only access your own object."

    def has_object_permission(self, request, view, obj):
        user = request.user

        if is_admin_or_staff(user):
            return True

        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == user


class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        if not is_authenticated(request.user):
            return False

        required_perm = getattr(view, "required_permission", None)
        if not required_perm:
            return False

        return request.user.has_perm(required_perm)


class CustomerVerificationRequired(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not is_authenticated(user):
            return False

        if is_admin_or_staff(user):
            return True

        if is_customer(user):
            return is_verified_customer(user)

        return False
