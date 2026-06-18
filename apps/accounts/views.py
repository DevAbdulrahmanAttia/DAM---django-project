from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView

from apps.orders.models import Order, OrderStatus
from apps.products.models import Product
from config.permissions import IsAdmin

from .models import EmailVerificationOTP, PasswordResetOTP, UserProfile
from .serializers import (
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
    VerifyResetOTPSerializer,
)
from .utils import issue_email_verification_otp, issue_password_reset_otp

User = get_user_model()

PASSWORD_RESET_SUCCESS_MESSAGE = (
    'If an account exists with this email, a reset code has been sent.'
)
RESEND_VERIFICATION_SUCCESS_MESSAGE = (
    'If an account exists and is not yet verified, a verification code has been sent.'
)


class AccountsHealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'accounts API is ready'},
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(TokenBlacklistView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user and not user.is_verified:
            issue_email_verification_otp(user)

        return Response(
            {'detail': RESEND_VERIFICATION_SUCCESS_MESSAGE},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response(
                {'detail': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_verified:
            return Response(
                {'detail': 'Email is already verified.'},
                status=status.HTTP_200_OK,
            )

        verification = (
            EmailVerificationOTP.objects.filter(user=user, otp=otp)
            .order_by('-created_at')
            .first()
        )

        if not verification or verification.is_expired:
            return Response(
                {'detail': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.save(update_fields=['is_verified'])
        EmailVerificationOTP.objects.filter(user=user).delete()

        return Response(
            {'detail': 'Email verified successfully.'},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user:
            issue_password_reset_otp(user)

        return Response(
            {'detail': PASSWORD_RESET_SUCCESS_MESSAGE},
            status=status.HTTP_200_OK,
        )


class VerifyResetOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response(
                {'detail': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_request = (
            PasswordResetOTP.objects.filter(
                user=user,
                otp=otp,
                is_verified=False,
            )
            .order_by('-created_at')
            .first()
        )

        if not reset_request or reset_request.is_expired:
            return Response(
                {'detail': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_request.is_verified = True
        reset_request.save(update_fields=['is_verified'])

        return Response(
            {
                'detail': 'Code verified successfully.',
                'reset_token': str(reset_request.reset_token),
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        password = serializer.validated_data['password']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response(
                {'detail': 'Invalid or expired reset request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_request = PasswordResetOTP.objects.filter(
            user=user,
            reset_token=reset_token,
            is_verified=True,
        ).first()

        if not reset_request or reset_request.is_expired:
            return Response(
                {'detail': 'Invalid or expired reset request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=['password'])
        reset_request.delete()

        return Response(
            {'detail': 'Password reset successfully.'},
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        partial = kwargs.pop('partial', False)

        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = UserProfileSerializer(
            request.user,
            context=self.get_serializer_context(),
        )
        return Response(read_serializer.data)


class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['username', 'email', 'phone', 'profile__full_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']

    def get_queryset(self):
        return User.objects.select_related('profile').annotate(
            _order_count=Count('orders'),
        )


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.select_related('profile')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AdminUserUpdateSerializer
        return AdminUserListSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = AdminUserUpdateSerializer(
            instance,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = AdminUserListSerializer(instance, context=self.get_serializer_context())
        return Response(read_serializer.data)


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        orders_qs = Order.objects.exclude(status=OrderStatus.CANCELLED)
        recent_orders = orders_qs.filter(created_at__gte=thirty_days_ago)

        revenue = orders_qs.aggregate(total=Sum('total'))['total'] or 0
        recent_revenue = recent_orders.aggregate(total=Sum('total'))['total'] or 0

        return Response(
            {
                'total_revenue': revenue,
                'recent_revenue': recent_revenue,
                'total_orders': orders_qs.count(),
                'recent_orders': recent_orders.count(),
                'total_products': Product.objects.filter(is_active=True).count(),
                'total_customers': User.objects.filter(role='customer', is_active=True).count(),
                'total_sellers': User.objects.filter(role='seller', is_active=True).count(),
                'pending_orders': Order.objects.filter(status=OrderStatus.PENDING).count(),
            },
            status=status.HTTP_200_OK,
        )
