# from django.db import models

# class User(models.Model):
#     name = models.CharField(max_length=255)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=255)
#     address = models.TextField()

#     def __str__(self):
#         return self.name

# class PaymentMethod(models.Model):
#     name = models.CharField(max_length=255)
#     details = models.TextField()

#     def __str__(self):
#         return self.name

# class Product(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     stock = models.IntegerField()

#     def __str__(self):
#         return self.name

# class Order(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     date = models.DateField(auto_now_add=True)
#     total = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)

#     def __str__(self):
#         return f"Pedido {self.id} - {self.user.name}"

# class OrderDetail(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     amount = models.IntegerField()
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.amount} x {self.product.name} en Pedido {self.order.id}"
    
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    address = models.TextField()

    def __str__(self):
        return self.name

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
