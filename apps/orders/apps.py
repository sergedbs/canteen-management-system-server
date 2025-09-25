from django.apps import AppConfig
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils import timezone


def order_confirmation_view(request):
    context = {
        **admin.site.each_context(request),
        "title": "Order Confirmation",
        "has_permission": True,
    }
    return render(request, "admin/orders/order_confirmation.html", context)


def order_search_view(request):
    from apps.orders.models import Order

    order_no = request.GET.get("order_no")
    if not order_no:
        return JsonResponse({"error": "Order number is required"}, status=400)

    try:
        order = (
            Order.objects.select_related("user", "menu")
            .prefetch_related("items__menu_item__item")
            .get(order_no=order_no)
        )

        # Check if order can be confirmed (pending and within menu time)
        can_confirm = order.status == "pending" and order.menu.start_time <= timezone.now() <= order.menu.end_time

        order_data = {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.get_status_display(),
            "user_email": order.user.email,
            "user_name": f"{order.user.first_name} {order.user.last_name}".strip() or order.user.email,
            "menu_name": order.menu.name,
            "total_amount": str(order.total_amount),
            "reservation_time": order.reservation_time.strftime("%Y-%m-%d %H:%M:%S")
            if order.reservation_time
            else None,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "can_confirm": can_confirm,
            "is_currently_active": order.menu.start_time <= timezone.now() <= order.menu.end_time,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.menu_item.item.name,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "total_price": str(item.total_price),
                }
                for item in order.items.all()
            ],
        }

        return JsonResponse({"order": order_data})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)


def order_confirm_view(request, order_no):
    from apps.orders.models import Order

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    order = get_object_or_404(Order, order_no=order_no)

    # Validate if order can be confirmed
    if order.status != "pending":
        return JsonResponse({"error": "Order is not in pending status"}, status=400)

    if not (order.menu.start_time <= timezone.now() <= order.menu.end_time):
        return JsonResponse({"error": "Order cannot be confirmed outside menu time"}, status=400)

    # Update order status
    order.status = "preparing"
    order.save()

    return JsonResponse(
        {
            "success": True,
            "message": f"Order {order_no} confirmed successfully",
            "new_status": order.get_status_display(),
        }
    )


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"

    def ready(self):
        # Apply decorators to views
        admin_order_confirmation_view = staff_member_required(login_required(order_confirmation_view))
        admin_order_search_view = staff_member_required(login_required(order_search_view))
        admin_order_confirm_view = staff_member_required(login_required(order_confirm_view))

        # Get the original get_urls method
        original_get_urls = admin.site.get_urls

        def get_urls():
            urls = original_get_urls()
            # Add custom URLs before the catch-all pattern
            custom_urls = [
                path("orders/confirmation/", admin_order_confirmation_view, name="order_confirmation"),
                path("orders/confirmation/search/", admin_order_search_view, name="search_order"),
                path("orders/confirmation/confirm/<str:order_no>/", admin_order_confirm_view, name="confirm_order"),
            ]
            # Return custom URLs first, then original URLs
            return custom_urls + urls

        # Override the admin site's get_urls method
        admin.site.get_urls = get_urls
