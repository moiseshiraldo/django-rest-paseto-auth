from django.urls import include, path


urlpatterns = [
    path('api/auth/', include('paseto_auth.urls', namespace='paseto_auth')),
]
