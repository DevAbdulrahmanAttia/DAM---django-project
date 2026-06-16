from django.urls import path

from .views import AccountsHealthCheckView

app_name = 'accounts'

urlpatterns = [
    path('health/', AccountsHealthCheckView.as_view(), name='health'),
]
