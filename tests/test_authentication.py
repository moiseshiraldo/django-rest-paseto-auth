import paseto
import pendulum

from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase
from django.test.client import RequestFactory

from rest_framework.exceptions import AuthenticationFailed

from paseto_auth import tokens
from paseto_auth.authentication import PasetoAuthentication
from paseto_auth.settings import AUTH_SETTINGS


class AuthenticationTestCase(TestCase):
    """
    Tests for the authentication scheme.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        token_claims = {
            'type': tokens.ACCESS,
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
        Test not auth attempt if invalid header.
        """
        request = self.fake_request({'HTTP_AUTHORIZATION': 'zxcvb'})
        self.assertEqual(PasetoAuthentication().authenticate(request), None)

    def test_invalid_access_token(self):
        """
        Test authentication scheme with invalid access token.
        """
        request = self.fake_request({'HTTP_AUTHORIZATION': 'Paseto zxcvb'})
        with self.assertRaises(AuthenticationFailed):
            PasetoAuthentication().authenticate(request)

    def test_expired_access_token(self):
        """
        Test authentication scheme with expired access token.
        """
        token_claims = {
            'type': tokens.ACCESS,
            'model': 'user',
            'pk': self.user.pk,
            'key': 'qwerty',
            'exp': pendulum.now().subtract(seconds=10).to_atom_string()
        }
        access_token = paseto.create(
            key=bytes.fromhex(AUTH_SETTINGS['SECRET_KEY']),
            purpose='local',
            claims=token_claims
        )
        auth_header = 'Paseto {}'.format(access_token.decode())
        request = self.fake_request({'HTTP_AUTHORIZATION': auth_header})
        with self.assertRaises(AuthenticationFailed):
            PasetoAuthentication().authenticate(request)

    def test_no_user_authentication(self):
        """
        Test authentication scheme with non-existent user.
        """
        self.user.delete()
        auth_header = 'Paseto {}'.format(self.access_token.decode())
        request = self.fake_request({'HTTP_AUTHORIZATION': auth_header})
        user, token = PasetoAuthentication().authenticate(request)
        self.assertFalse(user.is_authenticated)
        self.assertTrue(user.is_anonymous)

    def test_user_authentication(self):
        """
        Test authentication scheme with valid user access token.
        """
        auth_header = 'Paseto {}'.format(self.access_token.decode())
        request = self.fake_request({'HTTP_AUTHORIZATION': auth_header})
        user, token = PasetoAuthentication().authenticate(request)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(token.data['type'], 'access')

    def test_app_authentication(self):
        """
        Test authentication schem with valid app access token.
        """
        group = Group.objects.create(name="Test group")
        perm = Permission.objects.get(codename="add_userrefreshtoken")
        group.permissions.add(perm)
        obj, refresh_token = tokens.create_app_token(
            owner=self.user, groups=[group]
        )
        access_token = tokens.AccessToken(
            data={'model': 'app', 'pk': obj.pk, 'key': obj.key}
        )
        auth_header = 'Paseto {}'.format(str(access_token))
        request = self.fake_request({'HTTP_AUTHORIZATION': auth_header})
        user, token = PasetoAuthentication().authenticate(request)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(str(user), 'AppIntegrationUser')
        self.assertEqual(user.app_token.key, obj.key)
        self.assertTrue(user.has_perm('paseto_auth.add_userrefreshtoken'))
        self.assertTrue(user.has_module_perms('paseto_auth'))
        self.assertTrue(group in user.groups.all())
        self.assertFalse(perm in user.user_permissions.all())
        self.assertTrue(
            'paseto_auth.add_userrefreshtoken' in user.get_group_permissions()
        )
        self.assertTrue(
            'paseto_auth.add_userrefreshtoken' in user.get_all_permissions()
        )
