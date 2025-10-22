from django.urls import path, include
from rest_framework import routers
from main import views
from main.views import CartViewSet


router = routers.DefaultRouter()
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='payment-methods')
router.register(r'products', views.ProductViewSet, basename='products')
router.register(r'orders', views.OrderViewSet, basename='orders')
router.register(r'order-details', views.OrderDetailViewSet, basename='order-details')
router.register(r'user-product-records', views.UserProductRecordViewSet, basename='user-product-records')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')


cart_list = CartViewSet.as_view({"get": "list"})
add_item = CartViewSet.as_view({"post": "add_item"})
patch_item = CartViewSet.as_view({"patch": "patch_item", "delete": "delete_item"})
clear_cart = CartViewSet.as_view({"post": "clear"})
merge_cart = CartViewSet.as_view({"post": "merge"})

urlpatterns = [
    path('main/model/', include(router.urls)),
    path('main/model/admin-metrics/', views.AdminMetricsView.as_view(), name='admin-metrics'),
    path('main/model/checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('api/cart/', cart_list, name='cart-detail'),
    path('api/cart/items/', add_item, name='cart-add-item'),
    path('api/cart/items/<int:pk>/', patch_item, name='cart-patch-item'),
    path('api/cart/clear/', clear_cart, name='cart-clear'),
    path('api/cart/merge/', merge_cart, name='cart-merge'),
]
