from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
)
from .models import UserProfile
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer
from .utils import send_password_reset_email

User = get_user_model()


class AccountsHealthCheckView(APIView):
    """Placeholder view to verify the accounts API namespace."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'accounts API is ready'},
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    """Token view that uses CustomTokenObtainPairSerializer to block unverified users."""

    serializer_class = CustomTokenObtainPairSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """Return and update the authenticated user's profile data.

    GET returns user + profile fields (read serializer).
    PUT/PATCH update only the related UserProfile (write serializer).
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Keep existing behavior: return the authenticated User instance.
        return self.request.user

    def get_serializer_class(self):
        # Use a different serializer for update operations.
        if self.request.method in ("PUT", "PATCH"):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        # Ensure a UserProfile exists for the user, then update it.
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        partial = kwargs.pop("partial", False)

        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return the full read representation (User + profile fields).
        read_serializer = UserProfileSerializer(request.user, context=self.get_serializer_context())
        return Response(read_serializer.data)


class VerifyEmailView(APIView):
    """Handle email verification links."""

    permission_classes = []
    authentication_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            return Response({'detail': 'Email verified successfully.'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """Accepts an email and sends a password reset link if the user exists."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # user existence validated by serializer
        user = User.objects.get(email=serializer.validated_data['email'])

        # send password reset email
        send_password_reset_email(user, request)

        return Response({'detail': 'Password reset email sent.'}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    """Accepts uidb64, token and new password to reset the user's password."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)
