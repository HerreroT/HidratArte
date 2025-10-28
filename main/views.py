from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.apps import apps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.contrib.staticfiles import finders
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO


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
    NotificationSerializer,
)
from decimal import Decimal
from django.db.models import Sum
from django.contrib.auth import get_user_model
from rest_framework.views import APIView

from django.db import transaction
import logging

logger = logging.getLogger(__name__)

try:
    from .models import Notification  # type: ignore  # pragma: no cover
except Exception:  # pragma: no cover - absence tolerated
    Notification = None
    for app_label in ("main", "notifications"):
        try:
            Notification = apps.get_model(app_label, "Notification")
            if Notification is not None:
                break
        except Exception:
            Notification = None

def create_notification_safe(**kwargs):
    """Attempt to create a notification without breaking the main flow."""
    if Notification is None:
        return
    try:
        Notification.objects.create(**kwargs)
    except Exception:
        logger.exception("Notification creation failed", exc_info=True)


# WeasyPrint no necesita configuración externa

class AdminMetricsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        APPROVED_STATUSES = ['processing', 'shipped', 'delivered']

        total_products = Product.objects.count()
        total_users = get_user_model().objects.count()

        orders_qs = Order.objects.all()
        pending_count = orders_qs.filter(status='pending').count()
        approved_count = orders_qs.filter(status__in=APPROVED_STATUSES).count()
        canceled_count = orders_qs.filter(status='cancelled').count()

        total_sales = (
            orders_qs.filter(status__in=APPROVED_STATUSES)
            .aggregate(total=Sum('total'))
            .get('total') or 0
        )

        top_products_qs = (
            OrderDetail.objects.filter(order__status__in=APPROVED_STATUSES)
            .values('product_id', 'product__name')
            .annotate(units_sold=Sum('amount'))
            .order_by('-units_sold')[:6]
        )
        top_products = [
            {
                'product_id': item['product_id'],
                'name': item['product__name'],
                'units_sold': item['units_sold'],
            }
            for item in top_products_qs
        ]

        low_stock = [
            {'product_id': p.id, 'name': p.name, 'stock': p.stock}
            for p in Product.objects.filter(stock__lte=5).order_by('stock')[:8]
        ]

        response = {
            'total_products': total_products,
            'total_users': total_users,
            'orders': {
                'pending': pending_count,
                'approved': approved_count,
                'canceled': canceled_count,
            },
            'total_sales': float(total_sales),
            'top_products': top_products,
            'low_stock': low_stock,
        }
        return Response(response)

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [AdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AdminOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def create(self, request, *args, **kwargs):
        logger.debug(
            "Product create payload: data=%s files=%s",
            dict(request.data),
            {key: file.name for key, file in request.FILES.items()},
        )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        logger.debug(
            "Product update payload: data=%s files=%s",
            dict(request.data),
            {key: file.name for key, file in request.FILES.items()},
        )
        return super().update(request, *args, **kwargs)

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

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def confirm(self, request, pk=None):
        """Admin endpoint: confirm an order.

        This will check stock for each OrderDetail, decrement stock and move
        the order to 'processing'. If any product lacks sufficient stock,
        the operation is aborted and a 400 is returned describing the issue.
        """
        try:
            order = self.get_object()
        except Exception:
            return Response({"detail": "Order not found"}, status=404)

        if order.status != 'pending':
            return Response({'detail': 'Only pending orders can be confirmed.'}, status=400)

        with transaction.atomic():
            # collect shortages
            shortages = []
            details = OrderDetail.objects.filter(order=order)
            for d in details.select_related('product'):
                if d.product.stock < d.amount:
                    shortages.append({'product_id': d.product.id, 'name': d.product.name, 'available': d.product.stock, 'required': d.amount})

            if shortages:
                return Response({'detail': 'Stock insuficiente para alguno de los productos', 'shortages': shortages}, status=400)

            # decrement stock
            for d in details.select_related('product'):
                p = d.product
                p.stock -= d.amount
                p.save(update_fields=['stock'])

            order.status = 'processing'
            order.save(update_fields=['status'])

        return Response({'detail': 'Order confirmed and stock updated', 'order_id': order.id}, status=200)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def accept(self, request, pk=None):
        """Permitir que un administrador acepte un pedido y notificar al usuario."""
        try:
            order = self.get_object()
        except Exception:
            return Response({"detail": "Order not found"}, status=404)

        if order.status != 'pending':
            return Response({'detail': 'Solo se pueden aceptar pedidos pendientes.'}, status=400)

        with transaction.atomic():
            order.status = 'processing'
            order.save(update_fields=['status'])

            # Registrar notificación
            create_notification_safe(
                user=order.user,
                message=f"Tu pedido #{order.id} ha sido aceptado."
            )

        return Response({'detail': 'Pedido aceptado y notificación enviada', 'order_id': order.id}, status=200)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def cancel(self, request, pk=None):
        """Permitir que un administrador cancele un pedido y notificar al usuario."""
        try:
            order = self.get_object()
        except Exception:
            return Response({"detail": "Order not found"}, status=404)

        if order.status in ('shipped', 'delivered', 'cancelled'):
            return Response({'detail': f'No se puede cancelar un pedido con estado {order.status}.'}, status=400)

        with transaction.atomic():
            if order.status == 'processing':
                details = OrderDetail.objects.filter(order=order)
                for d in details.select_related('product').select_for_update():
                    p = d.product
                    p.stock = (p.stock or 0) + d.amount
                    p.save(update_fields=['stock'])

            order.status = 'cancelled'
            order.save(update_fields=['status'])

            # Registrar notificación
            create_notification_safe(
                user=order.user,
                message=f"Tu pedido #{order.id} ha sido cancelado."
            )

        return Response({'detail': 'Pedido cancelado y notificación enviada', 'order_id': order.id}, status=200)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Allow order owner or admin to cancel an order.

        If the order is already 'processing' we try to restore stock for each
        OrderDetail (this assumes the stock was previously decremented at
        confirmation). Cancellation of shipped/delivered orders is not allowed.
        """
        try:
            order = self.get_object()
        except Exception:
            return Response({"detail": "Order not found"}, status=404)

        user = request.user
        # only owner or admins can cancel
        if not (user.is_staff or order.user == user):
            return Response({"detail": "No autorizado a cancelar este pedido"}, status=403)

        if order.status in ('shipped', 'delivered', 'cancelled'):
            return Response({'detail': f'No se puede cancelar un pedido con estado {order.status}.'}, status=400)

        try:
            with transaction.atomic():
                # if the order was already processed and stock was decremented,
                # restore stock amounts
                if order.status == 'processing':
                    details = OrderDetail.objects.filter(order=order)
                    for d in details.select_related('product').select_for_update():
                        p = d.product
                        p.stock = (p.stock or 0) + d.amount
                        p.save(update_fields=['stock'])

                order.status = 'cancelled'
                order.save(update_fields=['status'])

            return Response({'detail': 'Pedido cancelado', 'order_id': order.id}, status=200)
        except Exception:
            logger.exception('Error cancelando order %s by user %s', getattr(order, 'id', None), getattr(user, 'id', None))
            return Response({'detail': 'Error al cancelar el pedido'}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_pdf(request, pk):
    "Generate a PDF invoice for an accepted order using ReportLab."
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('orderdetail_set__product'),
        pk=pk,
    )

    if not (request.user.is_staff or getattr(order, 'user_id', None) == request.user.id):
        return Response({'detail': 'Forbidden'}, status=403)

    allowed_statuses = {'accepted', 'aceptado', 'processing'}
    if str(order.status).lower() not in allowed_statuses:
        return Response({'detail': 'Invoice available only for accepted orders'}, status=400)

    # Preparar datos
    subtotal = Decimal('0.00')
    for detail in order.orderdetail_set.all():
        subtotal += detail.subtotal or Decimal('0.00')

    total = order.total or Decimal('0.00')
    shipping_cost = total - subtotal
    if shipping_cost < Decimal('0.00'):
        shipping_cost = Decimal('0.00')

    issued_at = getattr(order, 'created_at', None) or order.date
    invoice_number = f"F-{issued_at:%Y}-{order.id:06d}"

    # Generar PDF con ReportLab
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0a3d3f'),
            spaceAfter=30,
            alignment=1  # Center
        )
        elements.append(Paragraph('FACTURA', title_style))
        elements.append(Spacer(1, 12))
        
        # Info del negocio
        elements.append(Paragraph('<b>HidratArte</b>', styles['Normal']))
        elements.append(Paragraph('Gutiérrez 766, San Rafael, Mendoza', styles['Normal']))
        elements.append(Paragraph('tomasbajbuj@gmail.com', styles['Normal']))
        elements.append(Paragraph('+54 9 260 482 8418', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Info de la factura
        elements.append(Paragraph(f'<b>Factura N°:</b> {invoice_number}', styles['Normal']))
        elements.append(Paragraph(f'<b>Fecha:</b> {issued_at.strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Paragraph(f'<b>Cliente:</b> {order.user.username}', styles['Normal']))
        if order.shipping_address:
            elements.append(Paragraph(f'<b>Dirección:</b> {order.shipping_address}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Tabla de productos
        data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
        for detail in order.orderdetail_set.select_related('product'):
            quantity = detail.amount or 0
            unit_price = (detail.subtotal / quantity) if quantity else detail.subtotal
            data.append([
                detail.product.name,
                str(quantity),
                f'${float(unit_price):.2f}',
                f'${float(detail.subtotal):.2f}'
            ])
        
        table = Table(data, colWidths=[250, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3d3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Totales
        totals_data = [
            ['Subtotal:', f'${float(subtotal):.2f}'],
            ['Envío:', f'${float(shipping_cost):.2f}'],
            ['<b>TOTAL:</b>', f'<b>${float(total):.2f}</b>']
        ]
        totals_table = Table(totals_data, colWidths=[400, 130])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        elements.append(totals_table)
        
        # Construir PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return Response({'detail': 'Error al generar el PDF'}, status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice-{order.id}.pdf"'
    return response


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if Notification is None:
            return NotificationSerializer.Meta.model.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        queryset = self.get_queryset().filter(read=False)
        updated = queryset.update(read=True)
        return Response({"updated": updated})

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
        # Ensure product exists and use FK
        try:
            product = Product.objects.get(pk=data["product_id"])
        except Product.DoesNotExist:
            return Response({"detail": "Producto no encontrado"}, status=404)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
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
            # validate product exists
            try:
                product = Product.objects.get(pk=raw["product_id"])
            except Product.DoesNotExist:
                # skip non-existing products while merging
                logger.info('Skipping merge for non-existing product_id: %s', raw.get('product_id'))
                continue
            obj, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
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
        # Log the incoming request body and user for debugging
        try:
            logger.info('Checkout request received from user=%s; data=%s', getattr(user, 'id', None), request.data)
        except Exception:
            logger.exception('Failed to log checkout request data')
        # Additionally log raw body, headers and client IP (trimmed) to help debugging
        try:
            raw_body = request.body.decode('utf-8', errors='replace')
            # limit length to avoid huge logs
            logger.debug('Checkout raw body (trimmed to 5000 chars): %s', raw_body[:5000])
        except Exception:
            logger.exception('Failed to decode checkout raw body')
        try:
            headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_') or k in ('CONTENT_TYPE', 'CONTENT_LENGTH')}
            logger.debug('Checkout headers: %s', headers)
        except Exception:
            logger.exception('Failed to log checkout headers')
        try:
            ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR')
            logger.debug('Checkout client IP: %s', ip)
        except Exception:
            logger.exception('Failed to log client IP')
        if not isinstance(items, list) or len(items) == 0:
            return Response({'detail': 'No hay items para procesar.'}, status=400)

        # Log incoming items for debugging
        logger.debug('Checkout called by user %s with items: %s', getattr(user, 'id', None), items)

        # Parse and validate items explicitly, returning descriptive errors
        parsed = []
        for idx, raw in enumerate(items):
            # accept multiple possible keys sent by frontend
            pid = raw.get('product_id') or raw.get('productId') or raw.get('id')
            if pid is None or pid == "" or pid == 0:
                logger.warning('Invalid item at index %s: missing product id: %s', idx, raw)
                return Response({'detail': 'Item inválido: falta product_id', 'item': raw}, status=400)
            # parse qty defensively
            qty_raw = raw.get('qty') if 'qty' in raw else raw.get('quantity', 1)
            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                logger.warning('Invalid qty for item %s: %s', raw, qty_raw)
                return Response({'detail': 'Cantidad inválida en item', 'item': raw}, status=400)
            if qty <= 0:
                logger.warning('Invalid qty (<=0) for item %s', raw)
                return Response({'detail': 'Cantidad inválida (debe ser > 0) en item', 'item': raw}, status=400)
            parsed.append({'product_id': pid, 'qty': qty, 'raw': raw})

        # Calculate totals and validate stock
        subtotal = Decimal('0.00')
        prepared = []
        try:
            with transaction.atomic():
                for entry in parsed:
                    pid = entry['product_id']
                    qty = entry['qty']
                    try:
                        product = Product.objects.select_for_update().get(pk=pid)
                    except Product.DoesNotExist:
                        logger.warning('Product not found for pid %s (raw: %s)', pid, entry['raw'])
                        return Response({'detail': f'Producto no encontrado: {pid}', 'item': entry['raw']}, status=404)
                    if product.stock < qty:
                        logger.info('Insufficient stock for product %s: have %s, need %s', product.id, product.stock, qty)
                        return Response({'detail': f'Stock insuficiente para {product.name} (disponible: {product.stock})'}, status=400)
                    line_total = (product.price * qty)
                    subtotal += line_total
                    prepared.append({'product': product, 'qty': qty, 'subtotal': line_total})

                # Shipping rule: free over 50000 else 1000
                shipping = Decimal('0.00') if subtotal > Decimal('50000') else Decimal('1000')
                total = subtotal + shipping

                # Resolve payment method if provided
                payment_method = None
                if payment_method_id:
                    try:
                        payment_method = PaymentMethod.objects.get(pk=payment_method_id)
                    except PaymentMethod.DoesNotExist:
                        return Response({'detail': 'Método de pago inválido'}, status=400)

                # Create order in PENDING status (admin will confirm and decrement stock)
                order = Order.objects.create(user=user, total=total, payment_method=payment_method, shipping_address=shipping_address, status='pending')

                # Create order details (do NOT decrement stock here)
                for p in prepared:
                    OrderDetail.objects.create(
                        order=order,
                        product=p['product'],
                        amount=p['qty'],
                        subtotal=p['subtotal'],
                    )

                # Notify admins about the new pending order
                try:
                    from django.contrib.auth import get_user_model

                    admins = get_user_model().objects.filter(is_staff=True)
                    for admin in admins:
                        if getattr(admin, 'id', None) == getattr(user, 'id', None):
                            continue
                        create_notification_safe(
                            user=admin,
                            message=f"Nuevo pedido #{order.id} de {getattr(user, 'username', 'cliente')}"
                        )
                except Exception:
                    logger.exception('Failed to notify admins about new order %s', order.id)

                # Do not clear cart nor touch stock; admin must confirm the order
                return Response({'detail': 'Orden creada y pendiente de confirmación por el administrador', 'order_id': order.id}, status=201)
        except Product.DoesNotExist as e:
            logger.exception('Product not found during checkout for user %s: %s', getattr(user, 'id', None), e)
            return Response({'detail': 'Producto no encontrado'}, status=404)
        except ValueError as e:
            logger.exception('ValueError during checkout for user %s: %s', getattr(user, 'id', None), e)
            return Response({'detail': 'Datos de items inválidos'}, status=400)
        except Exception as e:
            # Catch-all to make sure we log unexpected errors with stack trace
            logger.exception('Unhandled exception during checkout for user %s: %s', getattr(user, 'id', None), e)
            return Response({'detail': 'Error interno durante checkout'}, status=500)



















