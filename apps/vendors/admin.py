from django.contrib import admin

from .models import Seller


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('store_name', 'user__username')
