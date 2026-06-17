from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartItemSerializer, CartSerializer


class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def _get_cart_queryset(self):
        return Cart.objects.prefetch_related('items__product')

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart = self._get_cart_queryset().get(pk=cart.pk)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = AddToCartSerializer(
            data=request.data,
            context={'cart': cart},
        )
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save(cart=cart)
        cart_item = CartItem.objects.select_related('product').get(pk=cart_item.pk)
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post', 'delete'], url_path='clear')
    def clear(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        deleted, _ = cart.items.all().delete()
        return Response(
            {'detail': f'Removed {deleted} item(s) from cart.'},
            status=status.HTTP_200_OK,
        )


class CartItemViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user).select_related(
            'product',
        )

    def partial_update(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
