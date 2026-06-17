from rest_framework import serializers

from .models import Seller


class SellerSerializer(serializers.ModelSerializer):
    """Serializer for the Seller model."""

    # Show the username of the linked user (read-only)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Seller
        fields = (
            'id',
            'user',
            'user_username',
            'store_name',
            'description',
            'is_approved',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'is_approved', 'created_at', 'updated_at')
