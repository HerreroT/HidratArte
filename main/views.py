from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import (
    PaymentMethod,
    Product,
    Order,
    OrderDetail,
    Cart,
    CartItem,
    UserProductRecord,
)
from .permissions import AdminOrReadOnly
from .serializer import (
    PaymentMethodSerializer,
    ProductSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    CartSerializer,
    CartItemSerializer,
    UserProductRecordSerializer,
)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [AdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AdminOrReadOnly]

    def get_queryset(self):
        qs = Product.objects.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    @action(detail=True, methods=["post"], url_path="set-stock", permission_classes=[IsAdminUser])
    def set_stock(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=404)
        try:
            stock = int(request.data.get("stock"))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid stock"}, status=400)
        if stock < 0:
            return Response({"detail": "Stock must be >= 0"}, status=400)
        product.stock = stock
        product.save(update_fields=["stock"])
        return Response({"id": product.id, "stock": product.stock}, status=200)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.all()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            qs = qs.filter(user=user)
        return qs


class OrderDetailViewSet(viewsets.ModelViewSet):
    queryset = OrderDetail.objects.all()
    serializer_class = OrderDetailSerializer


def get_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart = get_user_cart(request.user)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        cart = get_user_cart(request.user)
        data = request.data
        for k in ["product_id", "name", "price"]:
            if k not in data:
                return Response({"detail": f"Missing field: {k}"}, status=400)
        qty = max(int(data.get("qty", 1)), 1)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=data["product_id"],
            defaults={
                "name": data["name"],
                "price": data["price"],
                "qty": qty,
                "image": data.get("image", ""),
            },
        )
        if not created:
            item.qty += qty
            item.name = data.get("name", item.name)
            item.price = data.get("price", item.price)
            item.image = data.get("image", item.image)
            item.save()

        return Response(CartItemSerializer(item).data, status=201 if created else 200)

    @action(detail=True, methods=["patch"], url_path="items")
    def patch_item(self, request, pk=None):
        cart = get_user_cart(request.user)
        try:
            item = cart.items.get(pk=pk)
        except CartItem.DoesNotExist:
            return Response({"detail": "Item not found"}, status=404)

        if "qty" in request.data:
            qty = int(request.data["qty"])
            if qty <= 0:
                item.delete()
                return Response(status=204)
            item.qty = qty

        for f in ["name", "price", "image"]:
            if f in request.data:
                setattr(item, f, request.data[f])

        item.save()
        return Response(CartItemSerializer(item).data)

    @action(detail=True, methods=["delete"], url_path="items")
    def delete_item(self, request, pk=None):
        cart = get_user_cart(request.user)
        try:
            item = cart.items.get(pk=pk)
        except CartItem.DoesNotExist:
            return Response(status=204)
        item.delete()
        return Response(status=204)

    @action(detail=False, methods=["post"], url_path="clear")
    def clear(self, request):
        cart = get_user_cart(request.user)
        cart.items.all().delete()
        return Response({"detail": "Cart cleared"}, status=200)

    @action(detail=False, methods=["post"], url_path="merge")
    def merge(self, request):
        cart = get_user_cart(request.user)
        items = request.data.get("items", [])
        for raw in items:
            if not all(k in raw for k in ["product_id", "name", "price"]):
                continue
            qty = max(int(raw.get("qty", 1)), 1)
            obj, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=raw["product_id"],
                defaults={
                    "name": raw["name"],
                    "price": raw["price"],
                    "qty": qty,
                    "image": raw.get("image", ""),
                },
            )
            if not created:
                obj.qty += qty
                obj.name = raw.get("name", obj.name)
                obj.price = raw.get("price", obj.price)
                obj.image = raw.get("image", obj.image)
                obj.save()
        return Response(CartSerializer(cart).data, status=200)


class UserProductRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProductRecordSerializer

    def get_queryset(self):
        # Siempre mostrar solo el carrito del usuario actual
        return UserProductRecord.objects.select_related("product", "user").filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
