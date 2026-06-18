from django.urls import path

from .views import (
    VendorsHealthCheckView,
    SellerListCreateView,
    SellerDetailView,
    SellerMeView,
)

app_name = 'vendors'

urlpatterns = [
    path('health/', VendorsHealthCheckView.as_view(), name='health'),
    path('me/', SellerMeView.as_view(), name='seller-me'),
    path('', SellerListCreateView.as_view(), name='seller-list-create'),
    path('<int:pk>/', SellerDetailView.as_view(), name='seller-detail'),
]
