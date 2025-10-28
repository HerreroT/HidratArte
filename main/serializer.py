from rest_framework import serializers
from .models import PaymentMethod, Product, Order, OrderDetail, Cart, CartItem, UserProductRecord, Notification
from useradmin.serializer import UserSerializer

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'details']


class ProductSerializer(serializers.ModelSerializer):
    """
    Acepta archivo en:
      - image  (write-only, para que el front pueda mandar `image`)
      - image_upload (write-only, compat con tu versión anterior)
    Expone URL absoluta en:
      - image_url (read-only)
    """
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    image_upload = serializers.ImageField(write_only=True, required=False, allow_null=True)

    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock', 'category',
            'image', 'image_upload',   # entrada de archivo (no se devuelven)
            'image_url',               # salida con URL absoluta
        ]

    def get_image_url(self, obj):
        """
        Devuelve URL absoluta si hay imagen; None si no.
        Evita errores si la imagen no existe o no tiene .url.
        """
        try:
            if obj.image and getattr(obj.image, 'url', None):
                request = self.context.get('request')
                url = obj.image.url
                return request.build_absolute_uri(url) if request else url
        except Exception:
            return None
        return None

    def _pop_incoming_image(self, validated_data):
        """
        Prioridad: si vienen ambas, usa `image` y caso contrario `image_upload`.
        """
        file_obj = validated_data.pop('image', None)
        if file_obj is None:
            file_obj = validated_data.pop('image_upload', None)
        return file_obj

    def create(self, validated_data):
        file_obj = self._pop_incoming_image(validated_data)
        product = Product.objects.create(**validated_data)
        if file_obj:
            product.image = file_obj
            product.save(update_fields=['image'])
        return product

    def update(self, instance, validated_data):
        file_obj = self._pop_incoming_image(validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if file_obj is not None:
            instance.image = file_obj
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
        fields = ["id", "message", "created_at", "read"]
