from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from apps.menus.models import Menu
from apps.menus.paginators import WeeklyMenuPagination
from apps.menus.serializers import MenuSerializer


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
class MenusListView(generics.ListAPIView):
    serializer_class = MenuSerializer
    pagination_class = WeeklyMenuPagination

    def get_queryset(self):
        return Menu.objects.prefetch_related("menu_items__item").filter(start_time__gte=timezone.now())
