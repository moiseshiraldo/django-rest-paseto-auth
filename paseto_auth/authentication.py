from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import AuthenticationFailed
from rest_framework import authentication

from .models import AppRefreshToken, AppIntegrationUser
from .settings import AUTH_SETTINGS
from .tokens import AccessToken


class PasetoAuthentication(authentication.BaseAuthentication):
    """
    Paseto authentication scheme for Django Rest Framkwork.
    """

    def authenticate_header(self, request):
        return '{} realm="api"'.format(AUTH_SETTINGS['HEADER_PREFIX'])

    def authenticate(self, request):
        """
        Checks that the authentication header contains a valid access token.

        Returns:
            A tuple with the authenticated user and the access token.
        """
        if not request.META.get('HTTP_AUTHORIZATION'):
            return None
        try:
            token = request.META['HTTP_AUTHORIZATION'].split(" ")[1]
        except IndexError:
            raise AuthenticationFailed("Invalid access token")

        access_token = AccessToken(token=token)
        if not access_token.is_valid():
            raise AuthenticationFailed("Invalid access token")

        try:
            if access_token.data['model'] == 'user':
                user_model = get_user_model()
                user = user_model.objects.get(
                    pk=access_token.data['pk'],
                    is_active=True,
                )
            elif access_token.data['model'] == 'app':
                app_token = AppRefreshToken.objects.get(
                    pk=access_token.data['pk'],
                    locked=False
                )
                user = AppIntegrationUser(app_token)
        except ObjectDoesNotExist:
            raise AuthenticationFailed("Invalid access token")

        return (user, access_token)
