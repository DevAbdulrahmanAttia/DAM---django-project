from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order, OrderItem, OrderStatus
from config.permissions import IsSeller

from .models import Seller


class SellerStatsView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]

    def get(self, request):
        try:
            seller = request.user.seller_profile
        except Seller.DoesNotExist:
            return Response(
                {
                    'has_store': False,
                    'store_name': '',
                    'is_approved': False,
                    'total_products': 0,
                    'active_products': 0,
                    'total_orders': 0,
                    'pending_orders': 0,
                    'recent_orders': 0,
                    'total_revenue': '0.00',
                    'recent_revenue': '0.00',
                }
            )

        thirty_days_ago = timezone.now() - timedelta(days=30)
        items = OrderItem.objects.filter(seller=seller)
        orders = Order.objects.filter(items__seller=seller).distinct()

        revenue_agg = items.aggregate(
            total=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                Decimal('0'),
            )
        )
        recent_revenue_agg = items.filter(order__created_at__gte=thirty_days_ago).aggregate(
            total=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                Decimal('0'),
            )
        )

        return Response(
            {
                'has_store': True,
                'store_name': seller.store_name,
                'is_approved': seller.is_approved,
                'total_products': seller.products.count(),
                'active_products': seller.products.filter(is_active=True).count(),
                'total_orders': orders.count(),
                'pending_orders': orders.filter(
                    status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING],
                ).count(),
                'recent_orders': orders.filter(created_at__gte=thirty_days_ago).count(),
                'total_revenue': revenue_agg['total'],
                'recent_revenue': recent_revenue_agg['total'],
            }
        )
