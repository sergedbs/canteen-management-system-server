from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics

from apps.menus.models import Menu
from apps.menus.paginators import WeeklyMenuPagination
from apps.menus.serializers import MenuSerializer, MenuListResponseSerializer
#
#
# class MenusListView(generics.ListAPIView):
#     serializer_class = MenuSerializer
#
#     def get_queryset(self):
#         return Menu.objects.prefetch_related("menu_items__item").all()
#
#     def list(self, request, *args, **kwargs):
#         week_offset = int(request.query_params.get("week_offset", 0))
#
#         today = timezone.now().date()
#         target_date = today + timedelta(weeks=week_offset)
#         start_of_week = target_date - timedelta(days=target_date.weekday())
#         end_of_week = start_of_week + timedelta(days=6)
#
#         queryset = self.get_queryset().filter(date__range=[start_of_week, end_of_week]).order_by("start_time")
#         serializer = self.get_serializer(queryset, many=True)
#         response = serializer.data
#         navigation = {
#                 'current_week': '?week_offset=0',
#                 'next_week': f'?week_offset={week_offset + 1}'
#             }
#         if week_offset > 0:
#             navigation['previous_week'] = f'?week_offset={week_offset - 1}'
#         response['navigation'] = navigation
#
#         return Response(response)


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
class MenusListView(generics.RetrieveAPIView):
    serializer_class = MenuSerializer
    pagination_class = WeeklyMenuPagination

    def get_queryset(self):
        return Menu.objects.prefetch_related('menu_items__item').all()
