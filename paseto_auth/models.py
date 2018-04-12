from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import models


class AbstractRefreshToken(models.Model):
    """
    Abstract base model to store the state of refresh tokens.
    """
    user_agent = models.TextField(blank=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    locked = models.BooleanField(default=False)

    class Meta:
        abstract = True


class UserRefreshToken(AbstractRefreshToken):
    """
    Stores the state of a user refresh token.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )


class AppRefreshToken(AbstractRefreshToken):
    """
    Stores the state of an app integration refresh token.
    """
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name="app_token_set",
        related_query_name="app_token",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name="app_token_set",
        related_query_name="app_token",
    )


class AppIntegrationUser(AnonymousUser):
    """
    Anonymous user for app integrations.
    """
    def __init__(self, app_token):
        self.app_token = app_token

    def __str__(self):
        return 'AppIntegrationUser'

    @property
    def groups(self):
        return self.app_token.groups

    @property
    def user_permissions(self):
        return self.app_token.user_permissions
