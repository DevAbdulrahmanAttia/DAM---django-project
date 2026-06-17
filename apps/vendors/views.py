from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Seller
from .serializers import SellerSerializer


class VendorsHealthCheckView(APIView):
    """Placeholder view to verify the vendors API namespace."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'vendors API is ready'},
            status=status.HTTP_200_OK,
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow read access to anyone, write access only to the seller owner."""

    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS) are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for the owner
        return obj.user == request.user


class SellerListCreateView(generics.ListCreateAPIView):
    """
    GET  — List all approved sellers (anyone can view).
    POST — Create a seller profile (authenticated users only).
    """

    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Automatically set the user to the logged-in user
        serializer.save(user=self.request.user)


class SellerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — View a single seller profile (anyone).
    PUT    — Update seller profile (owner only).
    PATCH  — Partial update seller profile (owner only).
    DELETE — Delete seller profile (owner only).
    """

    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsOwnerOrReadOnly]
