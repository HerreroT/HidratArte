# from django.contrib import admin

# from.models import *

# admin.site.register(Usuario)
# admin.site.register(MetodoPago)
# admin.site.register(Producto)
# admin.site.register(DetallePedido)
from django.contrib import admin
from .models import User, PaymentMethod, Product, Order, OrderDetail

admin.site.register(User)
admin.site.register(PaymentMethod)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderDetail)