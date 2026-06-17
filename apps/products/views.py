from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Product, ProductImage, Review
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ReviewSerializer,
)


class ProductsHealthCheckView(APIView):
    """Placeholder view to verify the products API namespace."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'products API is ready'},
            status=status.HTTP_200_OK,
        )


# ─── Permissions ─────────────────────────────────────────────────────────────

class IsSellerOwnerOrReadOnly(permissions.BasePermission):
    """Only the seller who owns the product can edit/delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # obj is a Product — check if the logged-in user is the seller
        return obj.seller.user == request.user


class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    """Only the review author can edit/delete their review."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsImageOwnerOrReadOnly(permissions.BasePermission):
    """Only the seller who owns the product can manage its images."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.product.seller.user == request.user


# ─── Category Views ──────────────────────────────────────────────────────────

class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  — List all categories (anyone).
    POST — Create a new category (authenticated users).
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — View a category (anyone).
    PUT    — Update a category (authenticated).
    DELETE — Delete a category (authenticated).
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


# ─── Product Views (with Search & Filtering) ─────────────────────────────────

class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET  — List products with search and filtering (anyone).
    POST — Create a product (authenticated sellers).

    Search:   ?search=keyword  (searches name and description)
    Filter:   ?category=1&seller=2&is_active=true
    Ordering: ?ordering=price  or  ?ordering=-created_at
    """

    queryset = Product.objects.select_related('category', 'seller').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Filtering fields
    filterset_fields = ['category', 'seller', 'is_active']

    # Search fields
    search_fields = ['name', 'description']

    # Ordering fields
    ordering_fields = ['price', 'created_at', 'name']

    def get_serializer_class(self):
        return ProductListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Auto-set seller to the logged-in user's seller profile
        serializer.save(seller=self.request.user.seller_profile)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — View product details with images and reviews (anyone).
    PUT    — Update product (seller owner only).
    DELETE — Delete product (seller owner only).
    """

    queryset = Product.objects.select_related('category', 'seller').prefetch_related('images', 'reviews')
    serializer_class = ProductDetailSerializer
    permission_classes = [IsSellerOwnerOrReadOnly]


# ─── ProductImage Views ──────────────────────────────────────────────────────

class ProductImageListCreateView(generics.ListCreateAPIView):
    """
    GET  — List images for a specific product (anyone).
    POST — Upload an image for a product (authenticated seller owner).
    """

    serializer_class = ProductImageSerializer

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['product_id'])

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        product = Product.objects.get(pk=self.kwargs['product_id'])
        serializer.save(product=product)


class ProductImageDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    — View a product image (anyone).
    DELETE — Delete a product image (seller owner only).
    """

    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsImageOwnerOrReadOnly]


# ─── Review Views ─────────────────────────────────────────────────────────────

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET  — List reviews for a specific product (anyone).
    POST — Create a review for a product (authenticated users, one per product).
    """

    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_id'])

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        product = Product.objects.get(pk=self.kwargs['product_id'])
        serializer.save(user=self.request.user, product=product)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — View a review (anyone).
    PUT    — Update a review (author only).
    DELETE — Delete a review (author only).
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewOwnerOrReadOnly]
