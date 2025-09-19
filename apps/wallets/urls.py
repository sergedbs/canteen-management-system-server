from django.urls import path

from . import views

app_name = "wallets"

urlpatterns = [
    # customer "me" endpoints
    path("me/", views.WalletDetailMeView.as_view(), name="wallet-me"),
    path("me/transactions/", views.WalletTransactionsMeView.as_view(), name="wallet-transactions-me"),
    path(
        "me/transactions/<int:pk>/", views.WalletTransactionDetailMeView.as_view(), name="wallet-transaction-detail-me"
    ),
    # existing staff/admin endpoints
    # Wallet endpoints
    path("<uuid:user_id>/", views.WalletView.as_view(), name="wallet-detail"),
    path("<uuid:user_id>/deposit/", views.WalletDepositView.as_view(), name="wallet-deposit"),
    path("<uuid:user_id>/change/", views.WalletWithdrawView.as_view(), name="wallet-withdraw"),
    path("<uuid:user_id>/transactions/", views.WalletTransactionListView.as_view(), name="wallet-transactions"),
    path(
        "<uuid:user_id>/transactions/<int:pk>/",
        views.WalletTransactionDetailView.as_view(),
        name="wallet-transaction-detail",
    ),
]
