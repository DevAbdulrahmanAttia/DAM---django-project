from rest_framework import serializers

from apps.products.models import Product

from .models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'stock', 'is_active', 'primary_image')

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return None


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'unit_price', 'subtotal')
        read_only_fields = ('id', 'unit_price', 'subtotal')

    def validate_quantity(self, value):
        product = self.instance.product
        if not product.is_active:
            raise serializers.ValidationError('Product is no longer active.')
        if value > product.stock:
            raise serializers.ValidationError(
                f'Only {product.stock} items available in stock.'
            )
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.unit_price = instance.product.price
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Cart
        fields = (
            'id',
            'user_username',
            'user_email',
            'items',
            'item_count',
            'total_price',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_total_price(self, obj):
        return sum(item.subtotal for item in obj.items.all())

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            self.product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Product does not exist.')
        if not self.product.is_active:
            raise serializers.ValidationError('Product is not active.')
        return value

    def validate(self, attrs):
        product = self.product
        cart = self.context.get('cart')
        existing_qty = 0

        if cart is not None:
            existing_item = CartItem.objects.filter(cart=cart, product=product).first()
            if existing_item:
                existing_qty = existing_item.quantity

        total_qty = existing_qty + attrs['quantity']
        if total_qty > product.stock:
            available = product.stock - existing_qty
            if available <= 0:
                raise serializers.ValidationError(
                    {'quantity': 'Maximum available quantity is already in your cart.'}
                )
            raise serializers.ValidationError(
                {'quantity': f'Only {available} more item(s) can be added.'}
            )
        return attrs

    def save(self, **kwargs):
        cart = kwargs['cart']
        product = self.product
        quantity = self.validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'unit_price': product.price},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.unit_price = product.price
            cart_item.save()
        return cart_item
