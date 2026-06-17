from rest_framework import serializers

from .models import Category, Product, ProductImage, Review


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for the ProductImage model."""

    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', 'is_primary')
        read_only_fields = ('id', 'product')


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for the Review model."""

    # Show the username of the reviewer (read-only)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'product', 'user', 'user_username', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'product', 'user', 'created_at')


class ProductListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing products."""

    # Show category name and seller store name instead of just IDs
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_store_name = serializers.CharField(source='seller.store_name', read_only=True)

    # Show the primary image URL
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'price',
            'stock',
            'is_active',
            'category',
            'category_name',
            'seller',
            'seller_store_name',
            'primary_image',
            'created_at',
        )

    def get_primary_image(self, obj):
        """Return the URL of the primary image, or the first image if none is primary."""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail view — includes nested images and reviews."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_store_name = serializers.CharField(source='seller.store_name', read_only=True)

    # Nested related data
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'price',
            'stock',
            'is_active',
            'category',
            'category_name',
            'seller',
            'seller_store_name',
            'images',
            'reviews',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'seller', 'created_at', 'updated_at')
