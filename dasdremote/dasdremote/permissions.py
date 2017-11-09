from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthenticatedTest(BasePermission):
    """
    Allows access only to authenticated test user.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated() and request.user.username == settings.DASDREMOTE['TEST_USER']
