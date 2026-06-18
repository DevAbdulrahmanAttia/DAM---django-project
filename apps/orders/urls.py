from django.urls import path

from .views import (
    CheckoutView,
    OrderCancelView,
    OrderDetailView,
    OrderListView,
    OrderStatusUpdateView,
    OrdersHealthCheckView,
)
from .seller_views import SellerOrderDetailView, SellerOrderListView

app_name = 'orders'

urlpatterns = [
    path('health/', OrdersHealthCheckView.as_view(), name='health'),
    path('seller/', SellerOrderListView.as_view(), name='seller-list'),
    path('seller/<int:pk>/', SellerOrderDetailView.as_view(), name='seller-detail'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('', OrderListView.as_view(), name='list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='cancel'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='status-update'),
]
