from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CartItemViewSet, CartViewSet

app_name = 'cart'

router = DefaultRouter()
router.register(r'items', CartItemViewSet, basename='cart-item')
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
