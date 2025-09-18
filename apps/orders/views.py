from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import PermissionMixin, VerifiedOwnerMixin
from apps.orders.models import Order
from apps.orders.serializers import OrderCancelSerializer, OrderCreateSerializer
from apps.wallets.serializers import CapturePaymentSerializer, RefundPaymentSerializer


class OrderCreateView(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer


class OrderByIdView(APIView):
    def get(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderByNumberView(APIView):
    def get(self, request, order_no):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderProcessView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderCancelView(VerifiedOwnerMixin, generics.UpdateAPIView):
    """Cancel an order and release held funds. Only verified customers can cancel their own orders."""

    serializer_class = OrderCancelSerializer
    required_permission = "orders.change_order"
    lookup_url_kwarg = "orderId"

    def get_object(self):
        order_id = self.kwargs.get("orderId")
        return get_object_or_404(Order, id=order_id)


class CapturePaymentView(PermissionMixin, generics.CreateAPIView):
    serializer_class = CapturePaymentSerializer
    required_permission = "wallets.debit_balance"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        order_id = self.kwargs.get("orderId")
        order = get_object_or_404(Order, id=order_id)
        context["order"] = order
        return context

    def perform_create(self, serializer):
        order_id = self.kwargs.get("orderId")
        order = get_object_or_404(Order, id=order_id)
        serializer.save(order=order)


class RefundPaymentView(PermissionMixin, generics.CreateAPIView):
    serializer_class = RefundPaymentSerializer
    required_permission = "wallets.refund_payment"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        order_id = self.kwargs.get("orderId")
        order = get_object_or_404(Order, id=order_id)
        context["order"] = order
        return context

    def perform_create(self, serializer):
        order_id = self.kwargs.get("orderId")
        order = get_object_or_404(Order, id=order_id)
        serializer.save(order=order)
