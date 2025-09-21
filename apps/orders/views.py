from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.serializers import OrderCreateSerializer, OrderListSerializer


class OrderCreateView(ListCreateAPIView):
    queryset = Order.objects.all()

    def get_queryset(self):
        qs = Order.objects.select_related("menu").prefetch_related("items__menu_item__item")
        if self.request.method == "POST" or self.request.user.is_staff:
            return qs.all()
        return qs.filter(user=self.request.user).order_by("-reservation_time")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer


class OrderByIdView(APIView):
    def get(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderByNumberView(APIView):
    def get(self, request, order_no):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderProcessView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderCancelView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderRefundView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
