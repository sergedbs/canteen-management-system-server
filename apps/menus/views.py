from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.menus.models import Menu
from apps.menus.paginators import WeeklyMenuPagination
from apps.menus.serializers import MenuListResponseSerializer, MenuSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="week_offset",
            type=int,
            description="Week offset from current week (0 for current week, positive for future weeks)",
            default=0,
        ),
    ],
    responses={200: MenuListResponseSerializer},
)
class MenusListView(generics.ListAPIView):
    serializer_class = MenuSerializer
    pagination_class = WeeklyMenuPagination
    permission_classes = [
        AllowAny,
    ]
    authentication_classes = ()

    def get_queryset(self):
        return Menu.objects.prefetch_related("menu_items__item").filter(start_time__gte=timezone.now())
