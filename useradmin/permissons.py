from django.contrib.auth.models import User
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Solo los administradores pueden crear usuarios.
    Los usuarios normales solo pueden autenticarse (login).
    """

    def has_permission(self, request, view):
        # Permitir solo métodos de lectura (GET, HEAD, OPTIONS) a todos
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permitir crear usuarios solo a administradores
        if request.method == 'POST':
            return request.user and request.user.is_staff
        # Otros métodos (PUT, DELETE, etc.) solo para admin
        return request.user and request.user.is_staff
    