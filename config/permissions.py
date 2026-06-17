from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Allow access only to users with the admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Read for anyone; write for admins only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )
