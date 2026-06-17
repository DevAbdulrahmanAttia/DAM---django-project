from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import UserProfile

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

        return user


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