from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from .views import (
    LoginView,
    MFABackupCodesRegenerateView,
    MFADisableView,
    MFASetupConfirmView,
    MFASetupStartView,
    MFAVerifyView,
    RegisterView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("mfa/setup/start", MFASetupStartView.as_view(), name="mfa_setup_start"),
    path("mfa/setup/confirm", MFASetupConfirmView.as_view(), name="mfa_setup_confirm"),
    path("mfa/setup/regenerate", MFABackupCodesRegenerateView.as_view(), name="mfa_backup_codes_regenerate"),
    path("mfa/verify", MFAVerifyView.as_view(), name="mfa_verify"),
    path("mfa/disable", MFADisableView.as_view(), name="mfa_disable"),
]
