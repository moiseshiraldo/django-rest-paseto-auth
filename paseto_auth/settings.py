from django.conf import settings

user_settings = getattr(settings, 'PASETO_AUTH', {})

AUTH_SETTINGS = {
    'SECRET_KEY': settings.PASETO_KEY,
    'ACCESS_LIFETIME': min(user_settings.get('ACCESS_LIFETIME', 5*60), 10*60),
    'REFRESH_SHORT_LIFETIME': min(
        user_settings.get('REFRESH_SHORT_LIFETIME', 12*3600), 24*3600
    ),
    'REFRESH_LONG_LIFETIME': min(
        user_settings.get('REFRESH_LONG_LIFETIME', 30*24*3600), 60*24*3600
    ),
    'REFRESH_PERMANENT_LIFETIME': user_settings.get(
        'REFRESH_PERMANENT_LIFETIME', 2*365*24*3600
    )
}
