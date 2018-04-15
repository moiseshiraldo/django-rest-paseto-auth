import string
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import UserRefreshToken, AppRefreshToken
from .tokens import AccessToken, RefreshToken, LIFETIME_CHOICES


VALID_KEY_CHARS = string.ascii_lowercase + string.digits


class GetTokenPairSerializer(serializers.Serializer):
    """
    Gets a token pair if the user credentials are correct.

    Fields:
        username_field: username field of the configured user model.
        password: user password.
        remember: boolean to determine refresh token lifetime.
    """
    password = serializers.CharField(write_only=True)
    remember = serializers.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        """
        Sets username field from the configured user model.
        """
        super().__init__(*args, **kwargs)
        user_model = get_user_model()
        self.fields[user_model.USERNAME_FIELD] = serializers.CharField()

    def validate(self, data):
        """
        Validates user credentials.

        Args:
            data: serializer data.

        Returns:
            A dict containing a token pair.

        Raises:
            AuthenticationFailed if invalid user credentials.
        """
        self.user = authenticate(**data)
        if self.user is None or not self.user.is_active:
            raise AuthenticationFailed()
        tokens = self.get_tokens(data)
        return tokens

    def get_tokens(self, data):
        """
        Creates a token pair.

        Args:
            data: serializer data.

        Returns:
            A dict containing the access/refresh token pair.
        """
        self.claims = {
            'model': 'user',
            'pk': self.user.pk,
        }
        if data.get('remember'):
            self.claims['lifetime'] = 'long'
        else:
            self.claims['lifetime'] = 'short'
        self.claims['key'] = self.get_token_key()
        access_token = AccessToken(data=self.claims)
        refresh_token = RefreshToken(data=self.claims)
        return {
            'access_token': str(access_token),
            'refresh_token': str(refresh_token),
        }

    def get_token_key(self):
        """
        Creates a token key and stores the token state.

        Returns:
            A string containing the key.
        """
        while True:
            token_key = get_random_string(32, VALID_KEY_CHARS)
            if not UserRefreshToken.objects.filter(key=token_key).exists():
                lifetime = LIFETIME_CHOICES[self.claims['lifetime']]
                expires_at = datetime.now() + timedelta(seconds=lifetime)
                user_agent = self.context['request'].META.get(
                    'HTTP_USER_AGENT', ''
                )
                UserRefreshToken.objects.create(
                    key=token_key,
                    user=self.user,
                    user_agent=user_agent,
                    ip=self.get_user_ip(),
                    expires_at=expires_at,
                )
                return token_key

    def get_user_ip(self):
        """
        Determines the real user IP from the request headers.

        Returns:
            A string containing the user IP.
        """
        request = self.context['request']
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshTokenSerializer(serializers.Serializer):
    """
    Validates the refresh token and generates a new access one.

    Fields:
        refresh_token: a refresh token.

    Attributes:
        token_model: a dict mapping token types to their models.
    """
    refresh_token = serializers.CharField()
    refresh_model = {
        'user': UserRefreshToken,
        'app': AppRefreshToken,
    }

    def validate(self, data):
        """
        Generates a new access token if the refresh token is valid.

        Returns:
            A dict containing the new access token.

        Raises:
            AuthenticationFailed if the refresh token is invalid.
        """
        refresh_token = RefreshToken(token=data['refresh_token'])
        if refresh_token.is_valid():
            refresh_model = self.refresh_model[refresh_token.data['model']]
            try:
                refresh_model.objects.get(
                    key=refresh_token.data['key'], locked=False,
                )
            except ObjectDoesNotExist:
                raise AuthenticationFailed(detail="Invalid refresh token.")
        else:
            raise AuthenticationFailed(detail="Invalid refresh token.")

        access_token = AccessToken(data=refresh_token.data)
        return {'access_token': str(access_token)}
