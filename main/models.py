
from django.conf import settings 
from django.db import models


class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)
    details = models.TextField()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)

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
    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)
    image = models.URLField(blank=True)

    class Meta:
        unique_together = ("cart", "product_id")
