import unittest
import paseto
import pendulum

from paseto_auth import tokens, exceptions
from paseto_auth.settings import AUTH_SETTINGS


class TokenTestCase(unittest.TestCase):
    """
    Tests for token classes.
    """
    data = {
        'model': 'user',
        'pk': 13,
        'key': "qwerty",
        'lifetime': 'short'
    }

    def test_create_no_args(self):
        """
        Test exception raised if no data or token string argument.
        """
        with self.assertRaises(exceptions.TokenError):
            tokens.AccessToken()

    def test_create_access_token(self):
        """
        Test that access token is created correctly.
        """
        token = tokens.AccessToken(data=self.data)
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(token), 'utf-8'),
        )
        self.assertEqual(token.lifetime, AUTH_SETTINGS['ACCESS_LIFETIME'])
        self.assertEqual(parsed['message']['type'], tokens.ACCESS)
        self.assertEqual(parsed['message']['model'], self.data['model'])
        self.assertEqual(parsed['message']['pk'], self.data['pk'])

    def test_create_refresh_token(self):
        """
        Test that refresh token is created correctly.
        """
        token = tokens.RefreshToken(data=self.data)
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(token), 'utf-8'),
        )
        self.assertEqual(
            token.lifetime, AUTH_SETTINGS['REFRESH_SHORT_LIFETIME']
        )
        self.assertEqual(parsed['message']['type'], tokens.REFRESH)
        self.assertEqual(parsed['message']['model'], self.data['model'])
        self.assertEqual(parsed['message']['pk'], self.data['pk'])

    def test_parse_invalid_token(self):
        """
        Test invalid token string.
        """
        token = tokens.BaseToken(token="qwerty")
        self.assertFalse(token.is_valid())

    def test_parse_missing_claims(self):
        """
        Test invalid token missing claims.
        """
        data = self.data.copy()
        data.pop('model')
        token = tokens.AccessToken(data=data)
        token = tokens.AccessToken(token=str(token))
        self.assertFalse(token.is_valid())

    def test_parse_expired_token(self):
        """
        Test expired token.
        """
        data = self.data.copy()
        data['type'] = tokens.ACCESS
        data['exp'] = pendulum.now().subtract(seconds=10).to_atom_string()
        token = paseto.create(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            claims=data,
        )
        access_token = tokens.AccessToken(token=token.decode())
        self.assertFalse(access_token.is_valid())

    def test_parse_token(self):
        """
        Test valid token parsed correctly.
        """
        token = tokens.AccessToken(data=self.data)
        token = tokens.AccessToken(token=str(token))
        self.assertTrue(token.is_valid())
        self.assertEqual(token.data['type'], tokens.ACCESS)
        self.assertEqual(token.data['model'], self.data['model'])
