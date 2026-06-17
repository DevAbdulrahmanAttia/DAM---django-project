from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminCartListView, CartItemViewSet, CartViewSet

app_name = 'cart'

router = DefaultRouter()
router.register(r'items', CartItemViewSet, basename='cart-item')
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('admin/', AdminCartListView.as_view(), name='admin-list'),
    path('', include(router.urls)),
]
