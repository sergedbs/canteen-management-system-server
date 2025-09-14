from rest_framework.generics import CreateAPIView

from apps.orders.models import Order
from apps.orders.serializers import OrderCreateSerializer


class OrderCreateView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
