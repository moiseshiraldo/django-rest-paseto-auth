from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

import paseto
from rest_framework.exceptions import AuthenticationFailed

from paseto_auth.models import UserRefreshToken
from paseto_auth.serializers import (
    GetTokenPairSerializer,
    RefreshTokenSerializer,
)
from paseto_auth.settings import AUTH_SETTINGS


class SerializerTestCase(TestCase):
    """
    Tests for token serializers.
    """
    user_credentials = {
        'username': 'testuser',
        'password': 'qwerty'
    }

    def setUp(self):
        self.user = User.objects.create_user(**self.user_credentials)

    def fake_request(self, headers={}):
        factory = RequestFactory()
        request = factory.post('/api/auth/tokens/', **headers)
        return request

    def test_invalid_user_credentials(self):
        """
        Test invalid user credentials raise AuthenticationFailed.
        """
        serializer = GetTokenPairSerializer(data={
            'username': 'testuser',
            'password': '1234',
        })
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_get_user_ip(self):
        """
        Test get user IP from request.
        """
        serializer = GetTokenPairSerializer(
            data={}, context={'request': self.fake_request()}
        )
        self.assertEqual(serializer.get_user_ip(), '127.0.0.1')
        request = self.fake_request({'HTTP_X_FORWARDED_FOR': '42.42.42.42'})
        serializer = GetTokenPairSerializer(
            data={}, context={'request': request}
        )
        self.assertEqual(serializer.get_user_ip(), '42.42.42.42')

    def test_store_token_state(self):
        """
        Test that refresh token state is stored correctly.
        """
        request = self.fake_request(
            {'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64)'}
        )
        serializer = GetTokenPairSerializer(
            data={}, context={'request': request}
        )
        serializer.user = self.user
        serializer.claims = {'lifetime': 'short'}
        token_key = serializer.get_token_key()
        self.assertTrue(
            UserRefreshToken.objects.filter(key=token_key).exists()
        )
        token_state = UserRefreshToken.objects.get(key=token_key)
        self.assertEqual(
            token_state.user_agent, 'Mozilla/5.0 (X11; Linux x86_64)'
        )
        self.assertEqual(token_state.ip, '127.0.0.1')
        self.assertTrue(
            token_state.created_at + timedelta(days=1) > token_state.expires_at
        )

    def test_get_token_pair(self):
        """
        Test token pair generated successfully if correct user credentials.
        """
        serializer = GetTokenPairSerializer(
            data=self.user_credentials,
            context={'request': self.fake_request()},
        )
        self.assertTrue(serializer.is_valid())
        tokens = serializer.validated_data
        self.assertTrue(tokens.get('refresh_token'))
        self.assertTrue(tokens.get('access_token'))
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(tokens['refresh_token']), 'utf-8'),
        )
        token_key = parsed['message']['key']
        self.assertTrue(
            UserRefreshToken.objects.filter(key=token_key).exists()
        )

    def test_refresh_invalid_token(self):
        """
        Test AuthenticationFailed is raised if invalid token.
        """
        serializer = RefreshTokenSerializer(data={'refresh_token': 'zxcvb'})
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_locked_refresh_token(self):
        """
        Test AuthenticationFailed is raise if locked token.
        """
        serializer = GetTokenPairSerializer(
            data=self.user_credentials,
            context={'request': self.fake_request()},
        )
        self.assertTrue(serializer.is_valid())
        refresh_token = serializer.validated_data['refresh_token']
        UserRefreshToken.objects.update(locked=True)
        serializer = RefreshTokenSerializer(
            data={'refresh_token': refresh_token}
        )
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid()

    def test_get_access_token(self):
        """
        Test a new access token is generated successfully.
        """
        serializer = GetTokenPairSerializer(
            data=self.user_credentials,
            context={'request': self.fake_request()},
        )
        self.assertTrue(serializer.is_valid())
        refresh_token = serializer.validated_data['refresh_token']
        serializer = RefreshTokenSerializer(
            data={'refresh_token': refresh_token}
        )
        self.assertTrue(serializer.is_valid())
        access_token = serializer.validated_data['access_token']
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(access_token), 'utf-8'),
        )
        self.assertTrue(parsed['message']['type'], 'access')
