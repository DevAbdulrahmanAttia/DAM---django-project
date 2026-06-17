from django.urls import path

from .views import AccountsHealthCheckView, ProfileView

app_name = 'accounts'

urlpatterns = [
    path('health/', AccountsHealthCheckView.as_view(), name='health'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
