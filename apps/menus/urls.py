from django.urls import path

from apps.menus.views import MenusListView

app_name = "authentication"

urlpatterns = [
    path("menus", MenusListView.as_view(), name="menus-list"),
]
