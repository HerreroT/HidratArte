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
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.db import transaction
from decimal import Decimal
import logging


class AdminMetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        Product = globals().get('Product')
        Order = globals().get('Order')
        OrderDetail = globals().get('OrderDetail')

        # Basic counts
        total_products = Product.objects.count()
        out_of_stock = Product.objects.filter(stock__lte=0).count()
        low_stock_qs = Product.objects.filter(stock__lte=5).order_by('stock')[:8]
        low_stock = [{'id': p.id, 'name': p.name, 'stock': p.stock} for p in low_stock_qs]

        total_orders = Order.objects.count()
        total_sales = Order.objects.aggregate(sum=Sum('total'))['sum'] or 0

        # recent sales last 7 days
        since = timezone.now().date() - timedelta(days=7)
        recent_sales = Order.objects.filter(date__gte=since).aggregate(sum=Sum('total'))['sum'] or 0

        # users
        User = get_user_model()
        total_users = User.objects.count()

        # top selling products (by amount in OrderDetail)
        top_products = (
            OrderDetail.objects.values('product__id', 'product__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')[:6]
        )
        top_products_list = [
            {'product_id': p['product__id'], 'name': p['product__name'], 'sold': p['total_amount']}
            for p in top_products
        ]

        data = {
            'total_products': total_products,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'total_orders': total_orders,
            'total_sales': float(total_sales),
            'recent_sales_7d': float(recent_sales),
            'total_users': total_users,
            'top_products': top_products_list,
        }
        return Response(data)


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
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """Return only the orders belonging to the current user.

        This endpoint is used by the frontend 'Mis pedidos' view so admins
        won't see all orders in that view (admins can still access /admin/orders).
        """
        user = request.user
        qs = Order.objects.filter(user=user).order_by('-date')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Allow the order owner (or staff) to cancel an order if it's not yet shipped/delivered.

        Cancelling restores stock for the order details and sets status to 'cancelled'.
        """
        user = request.user
        try:
            # All select_for_update calls must be inside an atomic transaction
            with transaction.atomic():
                try:
                    order = Order.objects.select_for_update().get(pk=pk)
                except Order.DoesNotExist:
                    return Response({"detail": "Order not found"}, status=404)

                # Only owner or staff can cancel
                if not (user.is_staff or order.user == user):
                    return Response({"detail": "No permission to cancel this order"}, status=403)

                # Only allow cancelling if not shipped/delivered or already cancelled
                if order.status in ("shipped", "delivered", "cancelled"):
                    return Response({"detail": "No se puede cancelar este pedido en su estado actual."}, status=400)

                # Restore stock and set cancelled. Lock each product row before update.
                details = OrderDetail.objects.filter(order=order)
                for d in details:
                    try:
                        prod = Product.objects.select_for_update().get(pk=d.product_id)
                    except Product.DoesNotExist:
                        # If product was removed, skip stock restore but continue
                        logging.warning('Product %s referenced by order %s not found during cancel', d.product_id, pk)
                        continue
                    prod.stock = prod.stock + d.amount
                    prod.save(update_fields=['stock'])

                order.status = 'cancelled'
                order.save(update_fields=['status'])

        except Exception as e:
            logging.exception('Error cancelling order %s', pk)
            # Return the exception message to help debugging in development
            return Response({"detail": f"Error al cancelar el pedido: {str(e)}"}, status=500)

        return Response({"detail": "Pedido cancelado"}, status=200)


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


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        items = request.data.get('items') or []
        shipping_address = request.data.get('shipping_address')
        payment_method_id = request.data.get('payment_method_id')
        if not isinstance(items, list) or len(items) == 0:
            return Response({'detail': 'No hay items para procesar.'}, status=400)

        # Calculate totals and validate stock
        subtotal = Decimal('0.00')
        prepared = []
        try:
            with transaction.atomic():
                for raw in items:
                    pid = raw.get('product_id') or raw.get('productId') or raw.get('id')
                    qty = int(raw.get('qty') or raw.get('quantity') or 1)
                    if not pid or qty <= 0:
                        raise ValueError('Item inválido')
                    product = Product.objects.select_for_update().get(pk=pid)
                    if product.stock < qty:
                        return Response({'detail': f'Stock insuficiente para {product.name} (disponible: {product.stock})'}, status=400)
                    line_total = (product.price * qty)
                    subtotal += line_total
                    prepared.append({'product': product, 'qty': qty, 'subtotal': line_total})

                # Shipping rule: free over 10000 else 1000
                shipping = Decimal('0.00') if subtotal > Decimal('10000') else Decimal('1000')
                total = subtotal + shipping

                # Resolve payment method if provided
                payment_method = None
                if payment_method_id:
                    try:
                        payment_method = PaymentMethod.objects.get(pk=payment_method_id)
                    except PaymentMethod.DoesNotExist:
                        return Response({'detail': 'Método de pago inválido'}, status=400)

                # Create order
                order = Order.objects.create(user=user, total=total, payment_method=payment_method, shipping_address=shipping_address)

                # Create order details and decrement stock
                for p in prepared:
                    OrderDetail.objects.create(
                        order=order,
                        product=p['product'],
                        amount=p['qty'],
                        subtotal=p['subtotal'],
                    )
                    p['product'].stock -= p['qty']
                    p['product'].save(update_fields=['stock'])

                # Clear user's cart items
                try:
                    cart = Cart.objects.get(user=user)
                    cart.items.all().delete()
                except Cart.DoesNotExist:
                    pass

                return Response({'detail': 'Orden creada', 'order_id': order.id}, status=201)
        except Product.DoesNotExist:
            return Response({'detail': 'Producto no encontrado'}, status=404)
        except ValueError:
            return Response({'detail': 'Datos de items inválidos'}, status=400)
