from django.urls import path, include 
from rest_framework import routers
from useradmin import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    path('useradmin/', include(router.urls)),
    path('useradmin/login/', views.LoginView.as_view(), name='login'),
]
