from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from apps.authentication.views import (
    MFADisableView,
    MFARequestView,
    MFASetupView,
    MFAVerifyView,
    RegisterView,
    TokenWithRoleObtainPairView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenWithRoleObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("mfa/setup", MFASetupView.as_view(), name="mfa_setup"),
    path("mfa/request", MFARequestView.as_view(), name="mfa_request"),
    path("mfa/verify", MFAVerifyView.as_view(), name="mfa_verify"),
    path("mfa/disable", MFADisableView.as_view(), name="mfa_disable"),
]
