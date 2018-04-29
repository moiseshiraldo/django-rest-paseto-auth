import paseto
import pendulum

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APITestCase

from paseto_auth import tokens
from paseto_auth.models import UserRefreshToken
from paseto_auth.settings import AUTH_SETTINGS


class TokenViewTestCase(APITestCase):
    """
    Tests for token views
    """
    user_credentials = {
        'username': 'testuser',
        'password': 'qwerty'
    }

    def setUp(self):
        self.user = User.objects.create_user(**self.user_credentials)

    def test_invalid_user_credentials(self):
        """
        Test get token pair view with invalid user credentials.
        """
        response = self.client.post(
            reverse('paseto_auth:get_token_pair'),
            data={'username': 'testuser', 'password': '1234'}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()['detail'],
            'Incorrect authentication credentials.'
        )

    def test_get_token_pair(self):
        """
        Test get token pair view with valid user credentials.
        """
        response = self.client.post(
            reverse('paseto_auth:get_token_pair'),
            data=self.user_credentials,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('refresh_token'))
        self.assertTrue(response.json().get('access_token'))
        refresh_token = response.json()['refresh_token']
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(refresh_token), 'utf-8'),
        )
        token_key = parsed['message']['key']
        self.assertTrue(
            UserRefreshToken.objects.filter(key=token_key).exists()
        )

    def test_invalid_refresh_token(self):
        """
        Test get access token view with invalid refresh token.
        """
        response = self.client.post(
            reverse('paseto_auth:get_access_token'),
            data={'refresh_token': 'qwerty'},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'Invalid refresh token.')

    def test_expired_refresh_token(self):
        """
        Test get access token view with expired refresh token.
        """
        data = {
            'model': 'user',
            'pk': self.user.pk,
            'key': "qwerty",
            'type': tokens.REFRESH,
            'exp': pendulum.now().subtract(seconds=10).to_atom_string()
        }
        refresh_token = paseto.create(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            claims=data,
        )
        UserRefreshToken.objects.create(user=self.user, key=data['key'])
        response = self.client.post(
            reverse('paseto_auth:get_access_token'),
            data={'refresh_token': refresh_token.decode()},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'Invalid refresh token.')

    def test_get_access_token(self):
        """
        Test get access token view.
        """
        response = self.client.post(
            reverse('paseto_auth:get_token_pair'),
            data=self.user_credentials,
        )
        refresh_token = response.json()['refresh_token']
        response = self.client.post(
            reverse('paseto_auth:get_access_token'),
            data={'refresh_token': refresh_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('access_token'))
        access_token = response.json()['access_token']
        parsed = paseto.parse(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            token=bytes(str(access_token), 'utf-8'),
        )
        self.assertEqual(parsed['message']['type'], 'access')
