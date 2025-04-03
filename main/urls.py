from django.urls import path, include 
from rest_framework import routers
from main import views


router = routers.DefaultRouter()
router.register(r'usuarios', views.UsuarioView, basename='usuarios')
router.register(r'metodos_pago', views.MetodoPagoView, basename='metodos_pago')
router.register(r'productos', views.ProductoView, basename='productos')
router.register(r'pedidos', views.PedidoView, basename='pedidos')
router.register(r'detalles_pedido', views.DetallePedidoView, basename='detalles_pedido')

urlpatterns = [
    path('main/model/', include(router.urls))
]