from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import GetTokenPairSerializer, RefreshTokenSerializer
from .settings import AUTH_SETTINGS


class GetTokenPairView(GenericAPIView):
    """
    View for retrieving a token pair using user credentials.
    """
    serializer_class = GetTokenPairSerializer
    permission_classes = ()
    authentication_classes = ()

    def get_authenticate_header(self, request):
        return '{} realm="api"'.format(AUTH_SETTINGS['HEADER_PREFIX'])

    def post(self, request, *args, **kwargs):
        """
        Validates user credentials and returns response containing
        the token pair.

        Raises:
            AuthenticationFailed (401 response) if invalid user credentials.
        """
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class GetAccessTokenView(GenericAPIView):
    """
    View for retrieving a new access token using a refresh token.
    """
    serializer_class = RefreshTokenSerializer
    permission_classes = ()
    authentication_classes = ()

    def get_authenticate_header(self, request):
        return '{} realm="api"'.format(AUTH_SETTINGS['HEADER_PREFIX'])

    def post(self, request, *args, **kwargs):
        """
        Validates refresh token and returns response containing a new access
        token.

        Raises:
            AuthenticationFailed (401 response) if invalid refresh token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
