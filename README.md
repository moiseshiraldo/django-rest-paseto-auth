
# PASETO authentication for Django REST framework

Still in development. See https://github.com/paragonie/paseto for more information about PASETO.

## Motivations and objectives

I needed a token authentication system for a new project and none of the [available third party authentication pacakges](http://www.django-rest-framework.org/api-guide/authentication/#third-party-packages) covered my requirements completely. After some work developing my own system, I thought it would be interresting to share it and accept suggestions and contributions.

My goal is building a token authentication system that meets the following requirements:

- Secure and simple authentication using [Paseto (Platform-Agnostic SEcurity TOkens)](https://github.com/paragonie/paseto).
- Front-end agnostic (browser apps, mobile apps, etc).
- Suitable for user authentication and app integrations.
- Facilitates both reactive (blacklist tokens) and proactive (check IP, user-agent header, etc) security measures.
- Customisable token payloads, authentication conditions (transparent support for 2FA) and actions (i.e. check user login attempts).
