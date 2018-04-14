from django.urls import path

from .views import GetTokenPairView, GetAccessTokenView

app_name = 'paseto_auth'
urlpatterns = [
    path(
        'token/', GetTokenPairView.as_view(), name="get_token_pair"
    ),
    path(
        'token/refresh/', GetAccessTokenView.as_view(), name="get_access_token"
    ),
]
