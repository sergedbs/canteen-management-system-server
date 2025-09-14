from django.urls import path

from apps.orders.views import OrderCreateView

app_name = "orders"

urlpatterns = [
    path("orders", OrderCreateView.as_view(), name="order-create"),
]
