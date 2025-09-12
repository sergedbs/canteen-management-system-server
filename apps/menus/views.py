from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


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
class MenusView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


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
