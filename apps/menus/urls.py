from django.urls import path

from . import views

app_name = "menus"

urlpatterns = [
    # --- Items ---
    path("items", views.ItemsView.as_view()),  # GET list, POST create
    path("items/<uuid:itemId>", views.ItemDetailView.as_view()),  # GET, PATCH, DELETE
    # --- Categories ---
    path("categories", views.CategoriesView.as_view()),  # GET list, POST create
    path("categories/<uuid:id>", views.CategoryDetailView.as_view()),  # GET, PATCH, DELETE
    # --- Menus ---
    path("menus", views.MenusView.as_view()),  # GET list, POST create
    path("menus/<uuid:menuId>", views.MenuDetailView.as_view()),  # GET, PATCH, DELETE
    path("menus/<uuid:menuId>/items", views.MenuItemsView.as_view()),  # GET list, POST add
    path("menus/<uuid:menuId>/items/<uuid:itemId>", views.MenuItemDetailView.as_view()),  # GET, PATCH, DELETE
]
