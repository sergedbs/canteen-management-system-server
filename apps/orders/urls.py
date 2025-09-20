from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderCreateView.as_view()),  # GET list, POST create
    path("<uuid:orderId>", views.OrderByIdView.as_view()),  # GET order by ID
    path("find/<str:orderNo>", views.OrderByNumberView.as_view()),  # GET order by order number
    path("<uuid:orderId>/process", views.OrderProcessView.as_view()),  # POST
    path("<uuid:orderId>/capture", views.CapturePaymentView.as_view()),  # POST - Staff captures payment
    path("<uuid:orderId>/refund", views.RefundPaymentView.as_view()),  # POST - Staff refunds order
    path("me/<uuid:orderId>/cancel", views.OrderCancelMeView.as_view(), name="order-cancel-me"),
]
