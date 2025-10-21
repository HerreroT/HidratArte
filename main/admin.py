# from django.contrib import admin

# from.models import *

# admin.site.register(Usuario)
# admin.site.register(MetodoPago)
# admin.site.register(Producto)
# admin.site.register(DetallePedido)
from django.contrib import admin
from .models import PaymentMethod, Product, Order, OrderDetail

admin.site.register(PaymentMethod)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'image']
    list_filter = ['category']
    search_fields = ['name', 'description']
    
admin.site.register(Order)
admin.site.register(OrderDetail)