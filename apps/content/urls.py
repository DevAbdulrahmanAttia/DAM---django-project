from django.urls import path

from .views import (
    ContentHealthCheckView,
    BannerListCreateView,
    BannerDetailView,
    LandingPageView,
)

app_name = 'content'

urlpatterns = [
    path('health/', ContentHealthCheckView.as_view(), name='health'),
    path('landing/', LandingPageView.as_view(), name='landing'),
    path('banners/', BannerListCreateView.as_view(), name='banner-list-create'),
    path('banners/<int:pk>/', BannerDetailView.as_view(), name='banner-detail'),
]
