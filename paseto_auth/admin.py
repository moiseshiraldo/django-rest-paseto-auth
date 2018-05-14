from django.contrib import admin

from .models import UserRefreshToken, AppRefreshToken


class UserRefreshTokenAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user', 'key', 'user_agent', 'ip', 'created_at', 'expires_at'
    )
    list_display = ('user', 'key')
    list_select_related = True


class AppRefreshTokenAdmin(admin.ModelAdmin):
    readonly_fields = (
        'key', 'user_agent', 'ip', 'created_at', 'expires_at',
        'owner_ct', 'owner_id', 'owner', 'groups', 'user_permissions'
    )
    list_display = ('name', 'owner')
    list_select_related = True


admin.site.register(UserRefreshToken, UserRefreshTokenAdmin)
admin.site.register(AppRefreshToken, AppRefreshTokenAdmin)
