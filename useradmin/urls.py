from django.urls import path
from .views import LogoutJWTView, ProfileView, UserViewSet

urlpatterns = [
    path('jwt/logout/', LogoutJWTView.as_view(), name='jwt_logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserViewSet.as_view(), name='users'),  # Registro/listado
]
