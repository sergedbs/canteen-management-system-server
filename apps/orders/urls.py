from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("", views.OrdersView.as_view()),  # GET list, POST create
    path("<uuid:orderId>", views.OrderByIdView.as_view()),  # GET order by ID
    path("find/<str:orderNo>", views.OrderByNumberView.as_view()),  # GET order by order number
    path("<uuid:orderId>/process", views.OrderProcessView.as_view()),  # POST
    path("<uuid:orderId>/cancel", views.OrderCancelView.as_view()),  # POST
    path("<uuid:orderId>/refund", views.OrderRefundView.as_view()),  # POST
]
