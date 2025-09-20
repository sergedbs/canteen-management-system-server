from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import PermissionMixin, VerifiedCustomerMixin
from apps.orders.models import Order
from apps.orders.serializers import OrderCancelSerializer, OrderCreateSerializer
from apps.wallets.serializers import CapturePaymentSerializer, RefundPaymentSerializer


class _MeMixin(VerifiedCustomerMixin):
    def _bind_me(self, request):
        pass


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


@extend_schema(
    summary="Capture payment for order",
    description="Staff confirms customer pickup and captures payment.",
    operation_id="order_capture_payment",
    parameters=[
        OpenApiParameter(
            name="orderId",
            description="Order ID to capture payment for",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        ),
    ],
    request=CapturePaymentSerializer,
    responses={201: CapturePaymentSerializer},
    tags=["Orders", "Staff Operations"],
)
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


@extend_schema(
    summary="Refund order payment",
    description="Adds money back to customer balance, creates REFUND transaction, and cancels the order.",
    operation_id="order_refund_payment",
    parameters=[
        OpenApiParameter(
            name="orderId",
            description="Order ID to process refund for",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        ),
    ],
    request=RefundPaymentSerializer,
    responses={201: RefundPaymentSerializer},
    tags=["Orders", "Staff Operations"],
)
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


@extend_schema(
    summary="Cancel my order",
    description="Can only cancel PENDING or PREPARING orders (15 minutes before menu starts).",
    operation_id="order_me_cancel",
    parameters=[
        OpenApiParameter(
            name="orderId", description="Order ID to cancel", required=True, type=str, location=OpenApiParameter.PATH
        ),
    ],
    responses={200: OrderCancelSerializer},
    tags=["Orders"],
)
class OrderCancelMeView(_MeMixin, generics.UpdateAPIView):
    serializer_class = OrderCancelSerializer
    required_permission = "orders.change_order"
    lookup_url_kwarg = "orderId"

    def get_object(self):
        order_id = self.kwargs.get("orderId")
        return get_object_or_404(Order, id=order_id, user=self.request.user)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except (ValidationError, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
