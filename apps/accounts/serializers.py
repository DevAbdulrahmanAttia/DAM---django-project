from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )

    phone = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
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
            "username": {"required": True},
            "role": {"required": True},
        }

    def create(self, validated_data):
        username = validated_data.get("username")
        email = validated_data.get("email")
        phone = validated_data.get("phone")
        role = validated_data.get("role")
        password = validated_data.get("password")

        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            role=role,
            password=password,
        )

        return user