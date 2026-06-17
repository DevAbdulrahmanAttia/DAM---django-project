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