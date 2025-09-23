from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # Self profile (alias to user detail / user-specific endpoints)
    path("me", views.MeView.as_view(), name="me"),  # GET, PATCH
    path("me/password", views.MePasswordView.as_view()),
    path("me/balance", views.MeBalanceView.as_view()),
    path("me/orders", views.MeOrdersView.as_view()),
    path("me/transactions", views.MeTransactionsView.as_view()),
    # Admin / staff management
    # path("", views.UsersView.as_view()),  # GET list, POST create
    path("<uuid:id>", views.UserDetailView.as_view()),  # GET, PATCH, DELETE
    # path("<uuid:id>/password", views.UserPasswordAdminView.as_view()),  # PATCH
    # path("<uuid:id>/balance", views.UserBalanceView.as_view()),  # GET
    # path("<uuid:id>/orders", views.UserOrdersView.as_view()),  # GET
    # path("<uuid:id>/transactions", views.UserTransactionsView.as_view()),  # GET
    # Lookup by account number
    path("<str:accountNo>", views.UserByAccountNoView.as_view()),  # GET
]
