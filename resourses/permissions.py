from rest_framework.permissions import BasePermission
from users.models import User


class IsOrganisation(BasePermission):
    """
    Allows access only to users with 'organisation' or 'admin' role, or staff/superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [User.ORGANISATION])
        )
