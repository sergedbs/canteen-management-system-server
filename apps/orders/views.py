from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class OrdersView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderByIdView(APIView):
    def get(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderByNumberView(APIView):
    def get(self, request, order_no):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderProcessView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderCancelView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class OrderRefundView(APIView):
    def post(self, request, order_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
