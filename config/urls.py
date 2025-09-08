from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

swagger_urls = [
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

api_urls = [
    path("users/", include("apps.users.urls", namespace="users")),
    path("", include(swagger_urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
]
