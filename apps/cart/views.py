from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class CartHealthCheckView(APIView):
    """Placeholder view to verify the cart API namespace."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'cart API is ready'},
            status=status.HTTP_200_OK,
        )
