from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.authentication.views import (
    CookieRegisterView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    RegisterView,
    TokenWithRoleObtainPairView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenWithRoleObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Cookie-based endpoints
    path("register/cookie/", CookieRegisterView.as_view(), name="cookie_register"),
    path("login/cookie/", CookieTokenObtainPairView.as_view(), name="cookie_token_obtain_pair"),
    path("refresh/cookie/", CookieTokenRefreshView.as_view(), name="cookie_token_refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
]
