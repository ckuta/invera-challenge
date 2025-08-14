from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Custom permission to only allow owners of a task to view or edit it."""

    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return obj == request.user


class IsOwnerOrStaff(IsOwner):
    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True

        return super().has_object_permission(request, view, obj)


