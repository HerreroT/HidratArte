from rest_framework import serializers
from .models import PaymentMethod, Product, Order, OrderDetail, Cart, CartItem, UserProductRecord
from useradmin.serializer import UserSerializer


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'details']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category']

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
        
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product_id", "name", "price", "qty", "image"]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source="user", read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user_id", "items", "total", "updated_at"]

    def get_total(self, obj):
        return sum([item.price * item.qty for item in obj.items.all()])



class UserProductRecordSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source="user", read_only=True)
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True,
    )

    class Meta:
        model = UserProductRecord
        fields = ["id", "user_id", "product", "product_id", "quantity", "created_at", "updated_at"]
        read_only_fields = ["id", "user_id", "product", "created_at", "updated_at"]
