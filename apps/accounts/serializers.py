from django.contrib.auth import get_user_model
from django.db import transaction
import logging
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenObtainSerializer,
)

from .models import UserProfile
from .utils import issue_email_verification_otp

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    phone = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "role",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "username": {"required": True},
            "role": {"required": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                **validated_data,
            )

            UserProfile.objects.create(user=user)

        try:
            issue_email_verification_otp(user)
        except Exception:
            logger.exception('Verification email failed for %s', user.email)
            raise serializers.ValidationError(
                {
                    'detail': (
                        'Account created but verification email could not be sent. '
                        'Use POST /api/v1/auth/resend-verification/ to try again.'
                    ),
                }
            )

        return user


    def validate_password(self, value):
        """Validate password using Django's validators and return it.

        This ensures minimum length and non-numeric constraints defined
        in `AUTH_PASSWORD_VALIDATORS` are enforced and returned as
        serializer validation errors.
        """
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login with email; response includes role for client-side routing."""

    email = serializers.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        email = attrs.pop('email')
        try:
            user = User.objects.get(email__iexact=email)
            attrs[self.username_field] = user.get_username()
        except User.DoesNotExist:
            attrs[self.username_field] = email

        TokenObtainSerializer.validate(self, attrs)

        if not getattr(self.user, 'is_verified', False):
            raise serializers.ValidationError(
                {'detail': 'Please verify your email before logging in.'}
            )

        refresh = self.get_token(self.user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': self.user.role,
            'username': self.user.username,
            'email': self.user.email,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    # Read profile fields from the related UserProfile via the `profile` relation.
    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    address = serializers.CharField(source="profile.address", read_only=True)
    city = serializers.CharField(source="profile.city", read_only=True)
    country = serializers.CharField(source="profile.country", read_only=True)
    profile_image = serializers.ImageField(source="profile.profile_image", read_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone",
            "role",
            "full_name",
            "address",
            "city",
            "country",
            "profile_image",
        )


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating only the UserProfile fields."""

    class Meta:
        model = UserProfile
        fields = ("full_name", "address", "city", "country", "profile_image")
        extra_kwargs = {
            "profile_image": {"required": False, "allow_null": True},
        }


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_token = serializers.UUIDField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class AdminUserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='profile.full_name', read_only=True)
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone',
            'role',
            'is_active',
            'is_verified',
            'full_name',
            'date_joined',
            'order_count',
        )
        read_only_fields = fields

    def get_order_count(self, obj):
        return obj.orders.count()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active', 'is_verified')

    def validate(self, attrs):
        user = self.instance
        request = self.context.get('request')
        if user and request and user == request.user:
            if 'is_active' in attrs and not attrs['is_active']:
                raise serializers.ValidationError(
                    {'is_active': 'You cannot deactivate your own account.'}
                )
        return attrs