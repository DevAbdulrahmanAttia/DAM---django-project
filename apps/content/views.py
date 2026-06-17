from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.products.models import Category, Product
from apps.products.serializers import CategorySerializer, ProductListSerializer
from apps.vendors.models import Seller
from apps.vendors.serializers import SellerListSerializer
from config.permissions import IsAdminOrReadOnly

from .models import Banner
from .serializers import BannerSerializer


class ContentHealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({'detail': 'content API is ready'}, status=status.HTTP_200_OK)


class BannerListCreateView(generics.ListCreateAPIView):
    """
    GET  — List banners with search and filtering (anyone).
    POST — Create a banner (admin only).

    Search:   ?search=keyword
    Filter:   ?is_active=true
    Ordering: ?ordering=order  or  ?ordering=-created_at
    """

    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'subtitle']
    ordering_fields = ['order', 'created_at', 'title']
    ordering = ['order']


class BannerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsAdminOrReadOnly]


class LandingPageView(APIView):
    """Public endpoint aggregating homepage content."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')[:10]
        categories = Category.objects.all().order_by('name')[:8]
        products = (
            Product.objects.filter(is_active=True, seller__is_approved=True)
            .select_related('category', 'seller')
            .prefetch_related('images')
            .order_by('-created_at')[:8]
        )
        sellers = Seller.objects.filter(is_approved=True).order_by('-created_at')[:8]

        return Response(
            {
                'banners': BannerSerializer(banners, many=True, context={'request': request}).data,
                'categories': CategorySerializer(categories, many=True, context={'request': request}).data,
                'featured_products': ProductListSerializer(
                    products, many=True, context={'request': request}
                ).data,
                'sellers': SellerListSerializer(sellers, many=True, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )
