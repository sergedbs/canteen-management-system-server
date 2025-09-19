from django.urls import path

from . import views

app_name = "wallets"

urlpatterns = [
    # Wallet endpoints
    path("<uuid:user_id>/", views.WalletView.as_view(), name="wallet-detail"),
    path("<uuid:user_id>/deposit/", views.WalletDepositView.as_view(), name="wallet-deposit"),
    path("<uuid:user_id>/change/", views.WalletWithdrawView.as_view(), name="wallet-withdraw"),
    # Transactions under wallet
    path("<uuid:user_id>/transactions/", views.WalletTransactionListView.as_view(), name="wallet-transactions"),
    path(
        "<uuid:user_id>/transactions/<int:pk>/",
        views.WalletTransactionDetailView.as_view(),
        name="wallet-transaction-detail",
    ),
]
