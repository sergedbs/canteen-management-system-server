from django.urls import path

from .views import (
    EmailResendView,
    EmailVerifyView,
    LoginView,
    LogoutView,
    MFABackupCodesRegenerateView,
    MFADisableView,
    MFASetupConfirmView,
    MFASetupStartView,
    MFAVerifyView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("refresh/", RefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="token_blacklist"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("email/verify/", EmailVerifyView.as_view(), name="email_verify"),
    path("email/resend/", EmailResendView.as_view(), name="email_resend"),
    path("mfa/setup/start", MFASetupStartView.as_view(), name="mfa_setup_start"),
    path("mfa/setup/confirm", MFASetupConfirmView.as_view(), name="mfa_setup_confirm"),
    path("mfa/setup/regenerate", MFABackupCodesRegenerateView.as_view(), name="mfa_backup_codes_regenerate"),
    path("mfa/verify", MFAVerifyView.as_view(), name="mfa_verify"),
    path("mfa/disable", MFADisableView.as_view(), name="mfa_disable"),
    # Microsoft OAuth: Frontend handles full flow via MSAL, backend validates Bearer tokens
    # via MicrosoftBearerAuthentication class - no endpoints needed
]
