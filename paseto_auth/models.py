from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AbstractRefreshToken(models.Model):
    """
    Abstract base model to store the state of refresh tokens.
    """
    key = models.CharField(max_length=40, primary_key=True)
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

    def __str__(self):
        return self.key


class AppRefreshToken(AbstractRefreshToken):
    """
    Stores the state of an app integration refresh token.
    """
    name = models.CharField(max_length=100, blank=True)
    owner_ct = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    owner_id = models.PositiveIntegerField(blank=True, null=True)
    owner = GenericForeignKey('owner_ct', 'owner_id')
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

    def __str__(self):
        return self.name or self.key

    def get_group_permissions(self, obj=None):
        perms = Permission.objects.filter(group__app_token=self).values_list(
            'content_type__app_label', 'codename'
        ).order_by()
        return {"%s.%s" % (ct, name) for ct, name in perms}

    def get_all_permissions(self, obj=None):
        perms = self.user_permissions.values_list(
            'content_type__app_label', 'codename'
        ).order_by()
        return {
            *{"%s.%s" % (ct, name) for ct, name in perms},
            *self.get_group_permissions(obj),
        }

    def has_perm(self, perm, obj=None):
        return perm in self.get_all_permissions(obj)

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        return any(
            perm[:perm.index('.')] == app_label
            for perm in self.get_all_permissions()
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

    @property
    def is_authenticated(self):
        return True

    def get_group_permissions(self, obj=None):
        return self.app_token.get_group_permissions(obj)

    def get_all_permissions(self, obj=None):
        return self.app_token.get_all_permissions(obj)

    def has_perm(self, perm, obj=None):
        return self.app_token.has_perm(perm, obj)

    def has_perms(self, perm_list, obj=None):
        return self.app_token.has_perms(perm_list, obj)

    def has_module_perms(self, app_label):
        return self.app_token.has_module_perms(app_label)
