from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.permissions import IsAdmin

from .models import Order, OrderStatus
from .serializers import CheckoutSerializer, OrderSerializer, OrderStatusUpdateSerializer
from .services import CheckoutError, cancel_order, checkout_from_cart


class OrdersHealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({'detail': 'orders API is ready'}, status=status.HTTP_200_OK)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['id', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'total', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items__product').select_related('user')
        if getattr(self.request.user, 'role', None) == 'admin':
            return qs
        return qs.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items__product').select_related('user')
        if getattr(self.request.user, 'role', None) == 'admin':
            return qs
        return qs.filter(user=self.request.user)


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

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        qs = Order.objects.filter(pk=pk)
        if getattr(request.user, 'role', None) != 'admin':
            qs = qs.filter(user=request.user)

        try:
            order = qs.get()
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            cancel_order(order)
        except CheckoutError as exc:
            return Response(
                {'detail': exc.message, 'code': exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.prefetch_related('items__product').select_related('user').get(pk=order.pk)
        return Response(OrderSerializer(order).data)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            order = Order.objects.prefetch_related('items__product').select_related('user').get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        if new_status == OrderStatus.CANCELLED and order.status != OrderStatus.CANCELLED:
            try:
                cancel_order(order)
            except CheckoutError as exc:
                return Response(
                    {'detail': exc.message, 'code': exc.code},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])

        order = Order.objects.prefetch_related('items__product').select_related('user').get(pk=order.pk)
        return Response(OrderSerializer(order).data)
