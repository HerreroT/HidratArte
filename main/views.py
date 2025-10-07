
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    PaymentMethod,
    Product,
    Order,
    OrderDetail,
    Cart,
    CartItem,
)
from .serializer import (
    PaymentMethodSerializer,
    ProductSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    CartSerializer,
    CartItemSerializer,
)


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
