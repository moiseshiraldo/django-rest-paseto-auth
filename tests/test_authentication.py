from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

import paseto
from rest_framework.exceptions import AuthenticationFailed

from paseto_auth.authentication import PasetoAuthentication
from paseto_auth.settings import AUTH_SETTINGS


class AuthenticationTestCase(TestCase):
    """
    Tests for the authentication scheme.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        token_claims = {
            'type': 'access',
            'model': 'user',
            'pk': self.user.pk,
            'key': 'qwerty'
        }
        self.access_token = paseto.create(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            claims=token_claims,
            exp_seconds=5*60,
        )

    def fake_request(self, headers={}):
        factory = RequestFactory()
        request = factory.post('/api/view/', **headers)
        return request

    def test_invalid_authentication_header(self):
        """
        Test authentication scheme with invalid header.
        """
        request = self.fake_request({'HTTP_AUTHORIZATION': 'zxcvb'})
        with self.assertRaises(AuthenticationFailed):
            PasetoAuthentication().authenticate(request)

    def test_invalid_access_token(self):
        """
        Test authentication scheme with invalid access token.
        """
        request = self.fake_request({'HTTP_AUTHORIZATION': 'Paseto zxcvb'})
        with self.assertRaises(AuthenticationFailed):
            PasetoAuthentication().authenticate(request)

    def test_successful_authentication(self):
        """
        Test authentication scheme with valid access token.
        """
        auth_header = 'Paseto {}'.format(self.access_token.decode())
        request = self.fake_request({'HTTP_AUTHORIZATION': auth_header})
        user, token = PasetoAuthentication().authenticate(request)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(token.data['type'], 'access')
