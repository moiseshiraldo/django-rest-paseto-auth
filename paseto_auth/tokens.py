import paseto

from django import settings

from .settings import AUTH_SETTINGS


# Token types
ACCESS = 'access'
REFRESH = 'refresh'


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
    required_claims = ['type', 'model', 'pk']

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
            self.data = data
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
            key=bytes.fromhex(settings.PASETO_KEY),
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

    def __init__(self, data=None, token=None, remember=False):
        """
        Creates a token from the BaseToken class.
        
        Args:
            remember: boolean to set token lifetime to long/short (True/False).
        """
        if remember:
            self.lifetime = AUTH_SETTINGS['REFRESH_LONG_LIFETIME']
        else:
            self.lifetime = AUTH_SETTINGS['REFRESH_SHORT_LIFETIME']
        super().__init__(data, token)
