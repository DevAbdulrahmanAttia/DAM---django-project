from django.urls import path

from .views import VendorsHealthCheckView

app_name = 'vendors'

urlpatterns = [
    path('health/', VendorsHealthCheckView.as_view(), name='health'),
]
