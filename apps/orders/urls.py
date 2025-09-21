from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderCreateView.as_view()),  # GET list, POST create
    path("<uuid:order_id>", views.OrderByIdView.as_view()),  # GET order by ID
    path("find/<str:order_no>", views.OrderByNumberView.as_view()),  # GET order by order number
    path("<uuid:order_id>/process", views.OrderProcessView.as_view()),  # POST
    path("capture/", views.CapturePaymentView.as_view()),  # POST - Staff captures payment
    path("refund/", views.RefundPaymentView.as_view()),  # POST - Staff refunds order
    path("me/<uuid:order_id>/cancel", views.OrderCancelMeView.as_view(), name="order-cancel-me"),
]
