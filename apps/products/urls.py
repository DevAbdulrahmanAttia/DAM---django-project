from django.urls import path

from .views import (
    ProductsHealthCheckView,
    CategoryListCreateView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductImageListCreateView,
    ProductImageDetailView,
    ReviewListCreateView,
    ReviewDetailView,
)

app_name = 'products'

urlpatterns = [
    path('health/', ProductsHealthCheckView.as_view(), name='health'),

    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),

    # Products (with search & filtering)
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # Product Images (nested under product)
    path('<int:product_id>/images/', ProductImageListCreateView.as_view(), name='product-image-list-create'),
    path('images/<int:pk>/', ProductImageDetailView.as_view(), name='product-image-detail'),

    # Reviews (nested under product)
    path('<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
]
