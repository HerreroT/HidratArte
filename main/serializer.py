from rest_framework import serializers
from .models import PaymentMethod, Product, Order, OrderDetail, Cart, CartItem, UserProductRecord, Notification
from useradmin.serializer import UserSerializer


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'details']

class ProductSerializer(serializers.ModelSerializer):
    # Para lectura: URL completa
    image = serializers.SerializerMethodField(read_only=True)
    # Para escritura: archivo de imagen
    image_upload = serializers.ImageField(write_only=True, required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'image', 'image_upload']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def create(self, validated_data):
        image_upload = validated_data.pop('image_upload', None)
        product = Product.objects.create(**validated_data)
        if image_upload:
            product.image = image_upload
            product.save()
        return product
    
    def update(self, instance, validated_data):
        image_upload = validated_data.pop('image_upload', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if image_upload:
            instance.image = image_upload
        instance.save()
        return instance

class OrderDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = OrderDetail
        fields = ['id', 'order', 'product', 'amount', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    payment_method = PaymentMethodSerializer()
    order_detail = OrderDetailSerializer(source="orderdetail_set", many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'date', 'total', 'payment_method', 'order_detail', 'shipping_address', 'status']
        
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "name", "price", "qty", "image"]

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


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "created_at"]
