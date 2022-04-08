
# PASETO authentication for Django REST framework

[![PyPI version](https://badge.fury.io/py/django-rest-paseto-auth.svg)](https://badge.fury.io/py/django-rest-paseto-auth)
[![Build Status](https://travis-ci.org/moiseshiraldo/django-rest-paseto-auth.svg?branch=master)](https://travis-ci.org/moiseshiraldo/django-rest-paseto-auth)
[![Test coverage status](https://codecov.io/gh/moiseshiraldo/django-rest-paseto-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/moiseshiraldo/django-rest-paseto-auth)

Still in development, NOT READY for production.

Before using this, see https://github.com/paragonie/paseto for more information about PASETO and https://github.com/rlittlefield/pypaseto about the Python implementation.

## Motivations and objectives

I needed a token authentication system for a new project and none of the [available third party authentication pacakges](http://www.django-rest-framework.org/api-guide/authentication/#third-party-packages) covered my requirements completely. After some work developing my own system, I thought it would be interesting to share it and accept suggestions and contributions.

My goal is to build a token authentication system that meets the following requirements:

- Secure and simple authentication using [Paseto (Platform-Agnostic SEcurity TOkens)](https://github.com/paragonie/paseto).
- Front-end agnostic (browser apps, mobile apps, etc).
- Suitable for user authentication and app integrations.
- Facilitates both reactive (blacklist tokens) and proactive (check IP, user-agent header, etc) security measures.
- Customisable token payloads, authentication conditions (transparent support for 2FA) and actions (i.e. check user login attempts).

## Installation and configuration

Install using pip:

`pip install django-rest-paseto-auth`

Generate a 32-bytes hexadecimal secret key:

```python
import secrets
secrets.token_hex(32)
'55acd7321e85e62d0fe5ee6ea127ba4bd8ac90f6ea87f1bf2d3d5e816399d7d2'
```

Add it to your Django configuration and keep it as secured as the project's [SECRET_KEY](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY):

```python
PASETO_KEY = '55acd7321e85e62d0fe5ee6ea127ba4bd8ac90f6ea87f1bf2d3d5e816399d7d2'
```

Add `paseto_auth` to your installed applications:

```python
INSTALLED_APPS = (
    ...
    'paseto_auth',
)
```

And apply migrations:

`python manage.py migrate paseto_auth`

Include paseto auth URLs:

```python
from django.urls import include, path


urlpatterns = [
    path('api/auth/', include('paseto_auth.urls', namespace='paseto_auth')),
]
```

Finally, add the authentication scheme to the `REST_FRAMEWORK` configuration or the views you want to protect:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'paseto_auth.authentication.PasetoAuthentication',
    )
}
```

Optional configuration with default values:

```python
PASETO_AUTH = {
    'HEADER_PREFIX': 'Paseto',  # Prefix for the authentication header, e.g. Bearer
    'ACCESS_LIFETIME': 5*60,  # Max: 10*60 seconds
    'REFRESH_SHORT_LIFETIME': 12*3600,  # Max: 24*3600 seconds
    'REFRESH_LONG_LIFETIME': 30*24*3600,  # Max: 60*24*3600 seconds
    'REFRESH_PERMANENT_LIFETIME': 2*365*24*3600  # seconds
}

```

## Usage

To get a token pair from user credentials:

```shell
$ curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "qwerty", "remember": true}' \
  http://localhost:8000/api/auth/token/

----

{
  'access_token': 'v2.local.wSpANWW6wNkQoVhqCWRkUp-wPfoc6fFsml7kmNlmuccDdLpqpVKmOZy6C1cYttzIt0OM-DL2uOWQKcahje0u1uSceG5mzXBZVMjDZnbXZMamF5X5JDTCZrAruVSGZ5EtliHJTFkHkgvp8c3Xmut9_8fWI09Qn6U0gaWPgM8hM_eRi7FXNHvE7ZeGOrE37SImnVZm-jCGBgMYjWzOowzQ6ZH6JvaC07eWyh6zsGQGM-l65sBlbJtTHA',
  'refresh_token': 'v2.local.ZYSSnCB9Qc7FlABtXKq2Pl6uZ_Snd9P_iCBnxx18d1cYezN85fB40C_1YSr27lSVNdpeGX6usp8rEEnb3EHF5_B0sNfbG8HAoxqET0RDsVj9XSj5x8w-3jgHLzaHW-Zc6r9C_cY-wLRmMNL7obEq4ETwoYZTaLKcbxRH67GRCpQP1Rjil9ex9EGL6HKg26oJuxFG_hhlCzPYOMzgDDqUoQsl4AkdGq7fZzvZkBugXvVgY64s0TS2H10'
}

```

The `remember` parameter will determine the refresh token short/long lifetime (see configuration section).

To get a new access token:

```shell
$ curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "v2.local.ZYSSnCB9Qc7FlABtXKq2Pl6uZ_Snd9P_iCBnxx18d1cYezN85fB40C_1YSr27lSVNdpeGX6usp8rEEnb3EHF5_B0sNfbG8HAoxqET0RDsVj9XSj5x8w-3jgHLzaHW-Zc6r9C_cY-wLRmMNL7obEq4ETwoYZTaLKcbxRH67GRCpQP1Rjil9ex9EGL6HKg26oJuxFG_hhlCzPYOMzgDDqUoQsl4AkdGq7fZzvZkBugXvVgY64s0TS2H10"}' \
  http://localhost:8000/api/auth/token/refresh/

----

{
  'access_token': 'v2.local.wSpANWW6wNkQoVhqCWRkUp-wPfoc6fFsml7kmNlmuccDdLpqpVKmOZy6C1cYttzIt0OM-DL2uOWQKcahje0u1uSceG5mzXBZVMjDZnbXZMamF5X5JDTCZrAruVSGZ5EtliHJTFkHkgvp8c3Xmut9_8fWI09Qn6U0gaWPgM8hM_eRi7FXNHvE7ZeGOrE37SImnVZm-jCGBgMYjWzOowzQ6ZH6JvaC07eWyh6zsGQGM-l65sBlbJtTHA',
}

```

## App tokens

You can create user-independent refresh tokens for app integrations, with a pesudo-permanent lifetime (`PAESETO_AUTH['REFRESH_PERMANENT_LIFETIME']` setting) and custom Django groups/permissions. For example, to implement something like GitHub personal API tokens, you could do:

```python
from paseto_auth.tokens import create_app_token

obj, refresh_token = create_app_token(
   name="Custom application",
   owner=user,
   groups=groups,
   perms=permissions,
)
```

Where owner is a generic foreign key to any object. A reversed relation could look like:

```python
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class MyUserModel(models.Model):
    ...
    api_tokens = GenericRelation('paseto_auth.AppRefreshToken')
``` 

The `create_app_token` function returns the token object stored in the database and the refresh token string, that can be used to obtain access tokens an authenticate like a normal user. The authentication class will return an instance of `AppIntegrationUser` that implements all the methods from the Django `PermissionsMixin`.
