from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class AccountsHealthCheckView(APIView):
    """Placeholder view to verify the accounts API namespace."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response(
            {'detail': 'accounts API is ready'},
            status=status.HTTP_200_OK,
        )
