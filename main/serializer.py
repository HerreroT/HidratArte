from rest_framework import serializers
from .models import Usuario, MetodoPago, Producto, Pedido, DetallePedido

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'email', 'contraseña', 'direccion']

class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = ['id', 'nombre', 'detalles']

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock']

class DetallePedidoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer() 
    class Meta:
        model = DetallePedido
        fields = ['id', 'pedido', 'producto', 'cantidad', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer() 
    metodo_pago = MetodoPagoSerializer()  
    detalles_pedido = DetallePedidoSerializer(many=True, read_only=True)  

    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'fecha', 'total', 'metodo_pago', 'detalles_pedido']


