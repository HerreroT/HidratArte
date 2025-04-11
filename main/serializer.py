# from rest_framework import serializers
# from .models import Usuario, MetodoPago, Producto, Pedido, DetallePedido

# class UsuarioSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Usuario
#         fields = ['id', 'nombre', 'email', 'contraseña', 'direccion']

# class MetodoPagoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MetodoPago
#         fields = ['id', 'nombre', 'detalles']

# class ProductoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Producto
#         fields = ['id', 'nombre', 'descripcion', 'precio', 'stock']

# class DetallePedidoSerializer(serializers.ModelSerializer):
#     producto = ProductoSerializer() 
#     class Meta:
#         model = DetallePedido
#         fields = ['id', 'pedido', 'producto', 'cantidad', 'subtotal']

# class PedidoSerializer(serializers.ModelSerializer):
#     usuario = UsuarioSerializer() 
#     metodo_pago = MetodoPagoSerializer()  
#     detalles_pedido = DetallePedidoSerializer(many=True, read_only=True)  

#     class Meta:
#         model = Pedido
#         fields = ['id', 'usuario', 'fecha', 'total', 'metodo_pago', 'detalles_pedido']
from rest_framework import serializers
from .models import User, PaymentMethod, Product, Order, OrderDetail

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'address']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'details']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock']

class OrderDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = OrderDetail
        fields = ['id', 'order', 'product', 'amount', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    payment_method = PaymentMethodSerializer()
    order_detail = OrderDetailSerializer(many=True, read_only=True) 

    class Meta:
        model = Order
        fields = ['id', 'user', 'date', 'total', 'payment_method', 'order_detail']

