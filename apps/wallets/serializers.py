from rest_framework import serializers
from apps.wallets.models import Balance


class BalanceSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Balance
        fields = ["user", "current_balance", "on_hold", "available_balance"]

    def get_available_balance(self, obj):
        return str(obj.current_balance - obj.on_hold)

