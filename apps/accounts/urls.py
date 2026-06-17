from django.urls import path

from .views import (
    AccountsHealthCheckView,
    RegisterView,
    ProfileView,
    VerifyEmailView,
    CustomTokenObtainPairView,
    ForgotPasswordView,
    ResetPasswordConfirmView,
)

app_name = 'accounts'

urlpatterns = [
    path('health/', AccountsHealthCheckView.as_view(), name='health'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
]
