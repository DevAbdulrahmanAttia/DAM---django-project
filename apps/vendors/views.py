from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from config.permissions import IsAdmin

from .models import Seller
from .serializers import SellerSerializer


class VendorsHealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({'detail': 'vendors API is ready'}, status=status.HTTP_200_OK)


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(request.user, 'role', None) == 'admin':
            return True
        return obj.user == request.user


class SellerListCreateView(generics.ListCreateAPIView):
    """
    GET  — List sellers (approved only for public; all for admin).
    POST — Create a seller profile (authenticated users only).
    """

    serializer_class = SellerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_approved']
    search_fields = ['store_name', 'description']
    ordering_fields = ['store_name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Seller.objects.select_related('user').all()
        user = self.request.user
        if user.is_authenticated and getattr(user, 'role', None) == 'admin':
            return qs
        if self.request.method == 'GET':
            return qs.filter(is_approved=True)
        return qs

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SellerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.select_related('user').all()
    serializer_class = SellerSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdmin()]
        return [IsOwnerOrAdminOrReadOnly()]
