from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)
    details = models.TextField()

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = (
        ("agua", "Agua"),
        ("jugo", "Jugo"),
        ("gaseosa", "Gaseosa"),
        ("alcohol", "Alcohol"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="agua")
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    shipping_address = models.TextField(null=True, blank=True)
    STATUS_CHOICES = (
        ("pending", "Pendiente"),
        ("processing", "En proceso"),
        ("shipped", "Enviado"),
        ("delivered", "Entregado"),
        ("cancelled", "Cancelado"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Pedido {self.id} - {self.user.name}"


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.amount} x {self.product.name} en Pedido {self.order.id}"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    # Use a real foreign key to Product to prevent orphaned cart items at DB level
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="cart_items",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)
    image = models.URLField(blank=True)

    class Meta:
        unique_together = ("cart", "product")


class UserProductRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_records",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="user_records",
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User product record"
        verbose_name_plural = "User product records"

    def __str__(self):
        return f"{self.user} -> {self.product} ({self.quantity})"

    @staticmethod
    def _adjust_stock(product, delta):
        if delta > 0 and product.stock < delta:
            raise ValidationError("Stock insuficiente para completar la operación")
        product.stock -= delta
        product.save(update_fields=["stock"])

    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        with transaction.atomic():
            previous = None
            if self.pk:
                previous = (
                    UserProductRecord.objects.select_for_update()
                    .filter(pk=self.pk)
                    .first()
                )
            if previous and previous.product_id != self.product_id:
                old_product = (
                    Product.objects.select_for_update()
                    .get(pk=previous.product_id)
                )
                self._adjust_stock(old_product, -previous.quantity)
                previous_quantity = 0
            else:
                previous_quantity = previous.quantity if previous else 0

            product = Product.objects.select_for_update().get(pk=self.product_id)
            delta = self.quantity - previous_quantity
            if delta:
                self._adjust_stock(product, delta)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product_id)
            self._adjust_stock(product, -self.quantity)
            super().delete(*args, **kwargs)


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification({self.user}): {self.message[:40]}"
