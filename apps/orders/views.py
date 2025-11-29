from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import PermissionMixin, VerifiedCustomerMixin
from apps.orders.models import Order
from apps.orders.serializers import OrderCancelSerializer, OrderCreateSerializer, OrderListSerializer
from apps.wallets.serializers import CapturePaymentSerializer, RefundPaymentSerializer


class _MeMixin(VerifiedCustomerMixin):
    def _bind_me(self, request):
        pass


@extend_schema_view(
    get=extend_schema(
        summary="Staff: Get all orders. | Customer: Get personal orders.",
    ),
    post=extend_schema(summary="Customer: Place an order."),
)
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


@extend_schema(deprecated=True)
class OrderByIdView(APIView):
    def get(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


@extend_schema(summary="Staff: Get order by 6 character UPPERCASE code")
class OrderByNumberView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = OrderListSerializer
    lookup_field = "order_no"
    queryset = Order.objects.all()


@extend_schema(deprecated=True, description="Use `/orders/capture/` instead.")
class OrderProcessView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


@extend_schema(
    summary="Staff: Capture payment for order",
    description="Staff confirms customer pickup and captures payment: either order_id (UUID) or order_no.",
    operation_id="order_capture_payment",
    request=CapturePaymentSerializer,
    responses={201: CapturePaymentSerializer},
    tags=["orders"],
)
class CapturePaymentView(PermissionMixin, generics.CreateAPIView):
    serializer_class = CapturePaymentSerializer
    required_permission = "wallets.debit_balance"


@extend_schema(
    summary="Staff: Refund order payment",
    description="Staff processes refund for a paid order.",
    operation_id="order_refund_payment",
    request=RefundPaymentSerializer,
    responses={201: RefundPaymentSerializer},
    tags=["orders"],
)
class RefundPaymentView(PermissionMixin, generics.CreateAPIView):
    serializer_class = RefundPaymentSerializer
    required_permission = "wallets.refund_payment"


class OrderCancelMeView(_MeMixin, generics.UpdateAPIView):
    serializer_class = OrderCancelSerializer
    required_permission = "orders.change_order"
    lookup_url_kwarg = "order_id"

    def get_object(self):
        order_id = self.kwargs.get("order_id")
        return get_object_or_404(Order, id=order_id, user=self.request.user)

    @extend_schema(exclude=True)
    def put(self, request, *args, **kwargs):
        """Disable PUT method - use PATCH for partial updates only."""
        return Response(
            {"detail": "Use PATCH method for cancelling orders."}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @extend_schema(
        summary="Customer: Cancel my order",
        description="Can only cancel PENDING/PREPARING orders; must be at least 15 minutes before the menu starts.",
        operation_id="order_me_cancel",
        parameters=[
            OpenApiParameter(
                name="order_id",
                description="Order ID to cancel",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={
            200: OrderCancelSerializer,
        },
        tags=["orders"],
    )
    def patch(self, request, *args, **kwargs):
        try:
            return self.partial_update(request, *args, **kwargs)
        except (ValidationError, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
