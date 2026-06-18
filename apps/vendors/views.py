from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from config.permissions import IsAdmin, IsSeller

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


class SellerMeView(APIView):
    """GET/PATCH the authenticated seller's store profile; POST to create one."""

    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def _get_seller(self, user):
        try:
            return user.seller_profile
        except Seller.DoesNotExist:
            return None

    def get(self, request):
        seller = self._get_seller(request.user)
        if not seller:
            return Response({'detail': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SellerSerializer(seller, context={'request': request}).data)

    def post(self, request):
        if self._get_seller(request.user):
            return Response(
                {'detail': 'Seller profile already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SellerSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        seller = self._get_seller(request.user)
        if not seller:
            return Response({'detail': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SellerSerializer(
            seller,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
