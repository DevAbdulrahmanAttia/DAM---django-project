from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.vendors.models import Seller
from config.permissions import IsSeller

from .models import Order
from .serializers import SellerOrderSerializer


class SellerOrderListView(generics.ListAPIView):
    serializer_class = SellerOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['id', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_seller(self):
        return self.request.user.seller_profile

    def get_queryset(self):
        seller = self.get_seller()
        return (
            Order.objects.filter(items__seller=seller)
            .prefetch_related('items__product')
            .select_related('user')
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['seller'] = self.get_seller()
        return context

    def list(self, request, *args, **kwargs):
        try:
            request.user.seller_profile
        except Seller.DoesNotExist:
            return Response({'count': 0, 'next': None, 'previous': None, 'results': []})
        return super().list(request, *args, **kwargs)


class SellerOrderDetailView(generics.RetrieveAPIView):
    serializer_class = SellerOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    lookup_url_kwarg = 'pk'

    def get_seller(self):
        return self.request.user.seller_profile

    def get_queryset(self):
        seller = self.get_seller()
        return (
            Order.objects.filter(items__seller=seller)
            .prefetch_related('items__product')
            .select_related('user')
            .distinct()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['seller'] = self.get_seller()
        return context
