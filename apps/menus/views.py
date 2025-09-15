from django.db.models import Prefetch
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.constants import OrderStatus
from apps.menus.models import Menu, MenuItem
from apps.menus.paginators import WeeklyMenuPagination
from apps.menus.serializers import MenuSerializer
from apps.orders.models import OrderItem


# --- Items ---
class ItemsView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ItemDetailView(APIView):
    def get(self, request, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# --- Categories ---
class CategoriesView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class CategoryDetailView(APIView):
    def get(self, request, category_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, category_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, category_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# --- Menus ---
@extend_schema(
    parameters=[
        OpenApiParameter(
            name="week_offset",
            type=int,
            description="Week offset from current week (0 for current week, positive for future weeks)",
            default=0,
        ),
    ],
)
class MenusView(generics.ListAPIView):
    serializer_class = MenuSerializer
    pagination_class = WeeklyMenuPagination

    def get_queryset(self):
        return Menu.objects.prefetch_related(
            Prefetch(
                "menu_items",
                queryset=MenuItem.objects.select_related("item").prefetch_related(
                    Prefetch(
                        "order_items",
                        queryset=OrderItem.objects.filter(order__status__in=OrderStatus.active()),
                        to_attr="filtered_order_items",
                    )
                ),
            )
        ).filter(start_time__gte=timezone.now())

    # def post(self, request):
    #     return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MenuDetailView(APIView):
    def get(self, request, menu_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, menu_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, menu_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MenuItemsView(APIView):
    def get(self, request, menu_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request, menu_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MenuItemDetailView(APIView):
    def get(self, request, menu_id, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, menu_id, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, menu_id, item_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
