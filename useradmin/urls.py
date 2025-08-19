from django.urls import path
from .views import LogoutJWTView, ProfileView, UserViewSet, RegisterView, EmailLoginView

urlpatterns = [
    path('jwt/logout/', LogoutJWTView.as_view(), name='jwt_logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserViewSet.as_view(), name='users'),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', EmailLoginView.as_view(), name='token_obtain_pair'),  # <- Login por email
]
