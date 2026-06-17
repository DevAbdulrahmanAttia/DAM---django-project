from decimal import Decimal

from rest_framework import serializers

from apps.products.models import Product

from .models import Order, OrderItem


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'stock', 'is_active')


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            'id',
            'product',
            'seller',
            'quantity',
            'unit_price',
            'subtotal',
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'status',
            'status_display',
            'subtotal',
            'shipping_cost',
            'total',
            'items',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    shipping_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        required=False,
        default=Decimal('0'),
    )
