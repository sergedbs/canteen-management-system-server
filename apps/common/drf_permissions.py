from rest_framework import permissions

from .utils import is_admin_or_staff, is_authenticated, is_customer, is_verified_customer


class IsOwnerOrHasPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user

        # Owner check (support 'user' and 'owner')
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner is not None and owner == user:
            return True

        # View-level override (explicit global permission string)
        all_perm = getattr(view, "all_objects_permission", None)
        if all_perm:
            return user.has_perm(all_perm)

        # Fallback to default model-level permissions
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name

        if request.method in permissions.SAFE_METHODS:
            perm = f"{app_label}.view_{model_name}"
        else:
            perm = f"{app_label}.change_{model_name}"

        return user.has_perm(perm)


class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        if not is_authenticated(request.user):
            return False

        required_perm = getattr(view, "required_permission", None)
        if required_perm:
            return request.user.has_perm(required_perm)

        return True


class CustomerVerificationRequired(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not is_authenticated(user):
            return False

        if is_admin_or_staff(user):
            return True

        if is_customer(user):
            if request.method in permissions.SAFE_METHODS:
                return True
            return is_verified_customer(user)

        return False
