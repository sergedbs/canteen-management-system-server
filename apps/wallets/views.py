from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


# Wallet
class WalletView(APIView):
    def get(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class WalletDepositView(APIView):
    def post(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class WalletWithdrawView(APIView):
    def post(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# Wallet Transactions
class WalletTransactionListView(APIView):
    def get(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class WalletTransactionDetailView(APIView):
    def get(self, request, user_id, pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
