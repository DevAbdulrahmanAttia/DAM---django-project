from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenObtainSerializer,
)
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator

from .models import UserProfile
from .utils import send_verification_email

User = get_user_model()


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

            # Send verification email after transaction commits (if request is available).
            request = self.context.get('request')
            if request is not None:
                transaction.on_commit(lambda: send_verification_email(user, request))

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
    """Custom token serializer that blocks login for unverified users."""

    def validate(self, attrs):
        # Authenticate user first without generating tokens.
        TokenObtainSerializer.validate(self, attrs)

        # If the user hasn't verified email, deny login.
        if not getattr(self.user, 'is_verified', False):
            raise serializers.ValidationError(
                {'detail': 'Please verify your email before logging in.'}
            )

        # Now call parent to generate JWT tokens.
        return super().validate(attrs)


class UserProfileSerializer(serializers.ModelSerializer):
    # Read profile fields from the related UserProfile via the `profile` relation.
    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    address = serializers.CharField(source="profile.address", read_only=True)
    city = serializers.CharField(source="profile.city", read_only=True)
    country = serializers.CharField(source="profile.country", read_only=True)

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
        )


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating only the UserProfile fields."""

    class Meta:
        model = UserProfile
        fields = ("full_name", "address", "city", "country", "profile_image")
        extra_kwargs = {
            "profile_image": {"required": False, "allow_null": True},
        }


class ForgotPasswordSerializer(serializers.Serializer):
    """Accepts an email and validates that a user exists."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Validate uidb64 + token and reset the user's password."""

    uidb64 = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        uidb64 = attrs.get('uidb64')
        token = attrs.get('token')
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uidb64': 'Invalid uid.'})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({'token': 'Invalid or expired token.'})

        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        password = self.validated_data['password']
        user = self.validated_data['user']
        user.set_password(password)
        user.save()
        return user