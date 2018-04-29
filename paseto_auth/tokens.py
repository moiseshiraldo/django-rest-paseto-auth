import paseto
import string
from datetime import datetime, timedelta

from django.utils.crypto import get_random_string

from .exceptions import TokenError
from .models import UserRefreshToken, AppRefreshToken
from .settings import AUTH_SETTINGS


VALID_KEY_CHARS = string.ascii_lowercase + string.digits

# Token types
ACCESS = 'access'
REFRESH = 'refresh'

# Lifetime values
LIFETIME_CHOICES = {
    'short': AUTH_SETTINGS['REFRESH_SHORT_LIFETIME'],
    'long': AUTH_SETTINGS['REFRESH_LONG_LIFETIME'],
    'permanent': AUTH_SETTINGS['REFRESH_PERMANENT_LIFETIME'],
}


class BaseToken(object):
    """
    Base class for tokens.

    Attributes:
        required_claims: list of token required claims.
        token_type: token type (access/refresh).
        lifetime: token lifetime in seconds.

    Methods:
        is_valid: returns boolean indicating if the token is valid.
    """
    required_claims = ['type', 'model', 'pk', 'key']

    def __init__(self, data=None, token=None):
        """
        Creates a token object from a data dictionary or a token string.

        Args:
            data: optional dictionary containing the token claims.
            token: optional token string.

        Raises:
            TokenError: when missing both data and token args.
        """
        if data:
            self.data = data.copy()
            self.data['type'] = self.token_type
            self._create_token()
        elif token:
            self.token = token
        else:
            raise TokenError("Missing argument 'data' or 'token'")

    def _create_token(self):
        """
        Creates a token using paseto and assigns it to the token attribute.
        """
        token = paseto.create(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            claims=self.data,
            exp_seconds=self.lifetime,
        )
        self.token = token.decode()

    def _parse_token(self):
        """
        Parses the token string.

        Returns:
            A dict containing the token message, exp date and footer

        Raises:
            PasetoException: invalid token data.
            ValueError: invalid token string.
        """
        return paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(self.token, 'utf-8'),
            required_claims=self.required_claims,
        )

    def is_valid(self):
        """
        Indicates if the token is valid

        Returns:
            A boolean.
        """
        try:
            parsed = self._parse_token()
        except (paseto.PasetoException, ValueError):
            is_valid = False
        else:
            self.data = parsed['message']
            is_valid = self.data['type'] == self.token_type

        return is_valid

    def __str__(self):
        return self.token


class AccessToken(BaseToken):
    """
    Class for access tokens.
    """
    token_type = ACCESS
    lifetime = AUTH_SETTINGS['ACCESS_LIFETIME']


class RefreshToken(BaseToken):
    """
    Class for refresh tokens.
    """
    token_type = REFRESH

    def __init__(self, data=None, token=None):
        """
        Creates a token from the BaseToken class.

        Args:
            remember: boolean to set token lifetime to long/short (True/False).
        """
        if data:
            self.lifetime = LIFETIME_CHOICES[data['lifetime']]
        super().__init__(data, token)


def generate_token_key(refresh_token_type):
    """
    Creates a unique token key.

    Args:
        refresh_token_type: 'user' or 'app'.

    Returns:
        A string containing the key.
    """
    token_model = {
        'user': UserRefreshToken,
        'app': AppRefreshToken,
    }[refresh_token_type]
    while True:
        token_key = get_random_string(32, VALID_KEY_CHARS)
        if not token_model.objects.filter(key=token_key).exists():
            return token_key


def create_app_token(owner=None, groups=[], perms=[]):
    """
    Creates and stores an app refresh token.

    Args:
        owner: owner of the app token (generic ForeignKey).
        is_superuser: boolean to indicate superuser permissions.
        groups: list of groups to assign.
        perms: list of permissions to assign.

    Returns:
        The crated app token object.
    """
    token_key = generate_token_key(refresh_token_type='app')
    lifetime = LIFETIME_CHOICES['permanent']
    expires_at = datetime.now() + timedelta(seconds=lifetime)
    obj = AppRefreshToken.objects.create(
        owner=owner, key=token_key, expires_at=expires_at
    )
    if groups:
        obj.groups.add(*list(groups))
    if perms:
        obj.permissions.add(*list(perms))

    data = {
        'model': 'app',
        'key': token_key,
        'pk': token_key,
        'lifetime': 'permanent',
    }
    refresh_token = RefreshToken(data=data)

    return obj, str(refresh_token)
