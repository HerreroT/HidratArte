# from rest_framework import viewsets
# from .models import Usuario, MetodoPago, Producto, Pedido, DetallePedido
# from .serializer import UsuarioSerializer, MetodoPagoSerializer, ProductoSerializer, PedidoSerializer, DetallePedidoSerializer


# class UsuarioView(viewsets.ModelViewSet):
#     queryset = Usuario.objects.all()
#     serializer_class = UsuarioSerializer

# class MetodoPagoView(viewsets.ModelViewSet):
#     queryset = MetodoPago.objects.all()
#     serializer_class = MetodoPagoSerializer


# class ProductoView(viewsets.ModelViewSet):
#     queryset = Producto.objects.all()
#     serializer_class = ProductoSerializer

# class PedidoView(viewsets.ModelViewSet):
#     queryset = Pedido.objects.all()
#     serializer_class = PedidoSerializer

# class DetallePedidoView(viewsets.ModelViewSet):
#     queryset = DetallePedido.objects.all()
#     serializer_class = DetallePedidoSerializer
from rest_framework import viewsets
from .models import User, PaymentMethod, Product, Order, OrderDetail
from .serializer import UserSerializer, PaymentMethodSerializer, ProductSerializer, OrderSerializer, OrderDetailSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class OrderDetailViewSet(viewsets.ModelViewSet):
    queryset = OrderDetail.objects.all()
    serializer_class = OrderDetailSerializer