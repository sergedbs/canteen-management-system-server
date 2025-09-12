from datetime import timedelta

from django.utils import timezone
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class WeeklyMenuPagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.week_offset = int(request.query_params.get("week_offset", 0))
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week += timedelta(weeks=self.week_offset)
        end_of_week = start_of_week + timedelta(days=6)

        self.start_of_week = start_of_week
        self.end_of_week = end_of_week

        return queryset.filter(
            start_time__date__gte=start_of_week,
            end_time__date__lte=end_of_week,
        ).order_by("start_time")

    def get_paginated_response(self, data):
        def make_url(offset):
            return f"?week_offset={offset}"

        return Response(
            {
                "previous_week": make_url(self.week_offset - 1) if self.week_offset > 0 else None,
                "current_week": make_url(0),
                "next_week": make_url(self.week_offset + 1),
                "results": data,
            }
        )
