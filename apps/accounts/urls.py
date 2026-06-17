from django.urls import path

from .views import AccountsHealthCheckView, RegisterView, ProfileView

app_name = 'accounts'

urlpatterns = [
    path('health/', AccountsHealthCheckView.as_view(), name='health'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
