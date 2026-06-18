from django.urls import path

from .seller_views import SellerStatsView

app_name = 'seller'

urlpatterns = [
    path('stats/', SellerStatsView.as_view(), name='stats'),
]
