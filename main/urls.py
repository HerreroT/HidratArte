# from django.urls import path, include 
# from rest_framework import routers
# from main import views


# router = routers.DefaultRouter()
# router.register(r'usuarios', views.UsuarioView, basename='usuarios')
# router.register(r'metodos_pago', views.MetodoPagoView, basename='metodos_pago')
# router.register(r'productos', views.ProductoView, basename='productos')
# router.register(r'pedidos', views.PedidoView, basename='pedidos')
# router.register(r'detalles_pedido', views.DetallePedidoView, basename='detalles_pedido')

# urlpatterns = [
#     path('main/model/', include(router.urls))
# ]
from django.urls import path, include 
from rest_framework import routers
from main import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='payment-methods')
router.register(r'products', views.ProductViewSet, basename='products')
router.register(r'orders', views.OrderViewSet, basename='orders')
router.register(r'order-details', views.OrderDetailViewSet, basename='order-details')

urlpatterns = [
    path('main/model/', include(router.urls)),
]