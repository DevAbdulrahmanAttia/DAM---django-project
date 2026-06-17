from rest_framework import serializers

from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = (
            'id',
            'title',
            'subtitle',
            'image',
            'link_url',
            'button_text',
            'order',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
