from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.cart.models import Cart
from apps.products.models import Product

from .models import Order, OrderItem, OrderStatus


class CheckoutError(Exception):
    def __init__(self, message, code='checkout_error'):
        self.message = message
        self.code = code
        super().__init__(message)


@transaction.atomic
def checkout_from_cart(user, shipping_cost=Decimal('0')):
    cart = (
        Cart.objects.select_for_update()
        .filter(user=user)
        .prefetch_related('items__product__seller')
        .first()
    )

    if cart is None:
        raise CheckoutError('Cart is empty.', 'empty_cart')

    cart_items = list(cart.items.select_related('product', 'product__seller'))
    if not cart_items:
        raise CheckoutError('Cart is empty.', 'empty_cart')

    products = {
        item.product_id: Product.objects.select_for_update().get(pk=item.product_id)
        for item in cart_items
    }

    for item in cart_items:
        product = products[item.product_id]
        if not product.is_active:
            raise CheckoutError(
                f'Product "{product.name}" is no longer available.',
                'inactive_product',
            )
        if product.stock < item.quantity:
            raise CheckoutError(
                f'Insufficient stock for "{product.name}". Available: {product.stock}.',
                'insufficient_stock',
            )

    subtotal = sum(item.subtotal for item in cart_items)
    shipping_cost = Decimal(shipping_cost)
    total = subtotal + shipping_cost

    order = Order.objects.create(
        user=user,
        status=OrderStatus.CONFIRMED,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
    )

    order_items = [
        OrderItem(
            order=order,
            product=products[item.product_id],
            seller=products[item.product_id].seller,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)

    for item in cart_items:
        product = products[item.product_id]
        product.stock -= item.quantity
        product.save(update_fields=['stock', 'updated_at'])

    cart.items.all().delete()
    return Order.objects.prefetch_related('items__product').get(pk=order.pk)


@transaction.atomic
def cancel_order(order):
    if order.status == OrderStatus.CANCELLED:
        raise CheckoutError('Order is already cancelled.', 'already_cancelled')

    if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
        raise CheckoutError(
            'Cannot cancel an order that has already been shipped.',
            'cannot_cancel',
        )

    for item in order.items.select_related('product'):
        if item.product_id:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=['status', 'updated_at'])
    return Order.objects.prefetch_related('items__product').get(pk=order.pk)
