from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import CheckoutSerializer, OrderSerializer
from .services import CheckoutError, cancel_order, checkout_from_cart


class OrdersHealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'orders API is ready'},
            status=status.HTTP_200_OK,
        )


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related('items__product')
            .order_by('-created_at')
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__product',
        )


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = checkout_from_cart(
                user=request.user,
                shipping_cost=serializer.validated_data['shipping_cost'],
            )
        except CheckoutError as exc:
            return Response(
                {'detail': exc.message, 'code': exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            cancel_order(order)
        except CheckoutError as exc:
            return Response(
                {'detail': exc.message, 'code': exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(OrderSerializer(order).data)
