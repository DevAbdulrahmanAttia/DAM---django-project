from decimal import Decimal

from rest_framework import serializers

from apps.products.models import Product

from .models import Order, OrderItem, OrderStatus


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'stock', 'is_active')


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    seller_store_name = serializers.SerializerMethodField()
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
            'seller_store_name',
            'quantity',
            'unit_price',
            'subtotal',
        )
        read_only_fields = fields

    def get_seller_store_name(self, obj):
        return obj.seller.store_name if obj.seller else None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_username = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'user_username',
            'user_email',
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

    def get_user_username(self, obj):
        return obj.user.username if obj.user else None

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)


class CheckoutSerializer(serializers.Serializer):
    shipping_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        required=False,
        default=Decimal('0'),
    )


class SellerOrderSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    seller_subtotal = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_username = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'user_username',
            'user_email',
            'status',
            'status_display',
            'seller_subtotal',
            'items',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_user_username(self, obj):
        return obj.user.username if obj.user else None

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_items(self, obj):
        seller = self.context['seller']
        items = obj.items.filter(seller=seller)
        return OrderItemSerializer(items, many=True).data

    def get_seller_subtotal(self, obj):
        seller = self.context['seller']
        return sum(item.subtotal for item in obj.items.filter(seller=seller))
