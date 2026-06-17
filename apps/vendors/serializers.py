from rest_framework import serializers

from .models import Seller


class SellerListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = (
            'id',
            'user',
            'user_username',
            'store_name',
            'description',
            'logo',
            'is_approved',
            'product_count',
            'created_at',
        )
        read_only_fields = ('id', 'user', 'user_username', 'product_count', 'created_at')

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class SellerSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = (
            'id',
            'user',
            'user_username',
            'store_name',
            'description',
            'logo',
            'is_approved',
            'product_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and getattr(request.user, 'role', None) != 'admin':
            validated_data.pop('is_approved', None)
        return super().update(instance, validated_data)
