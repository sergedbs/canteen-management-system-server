from dataclasses import dataclass
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.common.constants import OrderStatus, TransactionStatus, TransactionType
from apps.orders.models import Order
from apps.wallets.models import Balance, Transaction

TWOPLACES = Decimal("0.01")


class WalletError(Exception):
    pass


@dataclass
class WalletResult:
    transaction: Transaction | None
    balance: Balance
    order: Order | None = None


def _quantize(amount: Decimal) -> Decimal:
    return (amount or Decimal("0")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _get_locked_balance_for_user(user) -> Balance:
    balance, _ = Balance.objects.get_or_create(user=user)
    return Balance.objects.select_for_update().get(pk=balance.pk)


def _get_locked_order(order_id) -> Order:
    try:
        return Order.objects.select_for_update().get(id=order_id)
    except ObjectDoesNotExist as err:
        raise WalletError("Order not found.") from err


@transaction.atomic
def deposit(user, amount: Decimal) -> WalletResult:
    amount = _quantize(amount)
    if amount <= 0:
        raise WalletError("Amount must be positive.")

    balance = _get_locked_balance_for_user(user)

    Balance.objects.filter(pk=balance.pk).update(current_balance=F("current_balance") + amount)
    balance.refresh_from_db(fields=["current_balance", "on_hold"])

    tx = Transaction.objects.create(
        balance=balance,
        type=TransactionType.DEPOSIT,
        amount=amount,
        remaining_balance=balance.current_balance,
        order=None,
        status=TransactionStatus.COMPLETED,
    )
    return WalletResult(transaction=tx, balance=balance)


@transaction.atomic
def place_hold(user, order_id) -> WalletResult:
    order = _get_locked_order(order_id)

    if order.user_id != user.id:
        raise WalletError("You can only place a hold on your own order.")

    if order.status != OrderStatus.PENDING:
        raise WalletError("Order must be pending to place a hold.")

    balance = _get_locked_balance_for_user(user)

    available = balance.current_balance - balance.on_hold
    if available < order.total_amount:
        raise WalletError("Insufficient available funds to place hold.")

    Balance.objects.filter(pk=balance.pk).update(on_hold=F("on_hold") + order.total_amount)
    balance.refresh_from_db(fields=["current_balance", "on_hold"])

    tx = Transaction.objects.create(
        balance=balance,
        type=TransactionType.HOLD,
        amount=order.total_amount,
        remaining_balance=balance.current_balance,
        order=order,
        status=TransactionStatus.PENDING,
    )

    order.status = OrderStatus.CONFIRMED
    order.save(update_fields=["status"])

    return WalletResult(transaction=tx, balance=balance, order=order)


@transaction.atomic
def capture_payment_by_staff(user, order_id) -> WalletResult:
    """
    Staff confirms pickup: move funds from hold to spent.
    - on_hold -= amount
    - current_balance -= amount
    - update HOLD transaction to PAYMENT with COMPLETED status
    - order -> PAID
    """
    order = _get_locked_order(order_id)

    if order.status not in (OrderStatus.PREPARING, OrderStatus.CONFIRMED, OrderStatus.PENDING):
        raise WalletError("Order is not in a payable state.")

    balance = _get_locked_balance_for_user(order.user)

    amount = _quantize(order.total_amount)

    if order.status in (OrderStatus.PREPARING, OrderStatus.CONFIRMED):
        if balance.on_hold < amount:
            raise WalletError("Insufficient held funds for this order.")

        Balance.objects.filter(pk=balance.pk).update(
            on_hold=F("on_hold") - amount,
            current_balance=F("current_balance") - amount,
        )
    else:
        hold_transaction = Transaction.objects.filter(
            balance=balance, order=order, type=TransactionType.HOLD, status=TransactionStatus.PENDING
        ).first()

        if not hold_transaction:
            raise WalletError("Cannot capture a PENDING order without a hold transaction.")

        if balance.current_balance < amount:
            raise WalletError("Insufficient funds for this order.")

        Balance.objects.filter(pk=balance.pk).update(
            current_balance=F("current_balance") - amount,
        )

    balance.refresh_from_db(fields=["current_balance", "on_hold"])

    # Find and update the existing HOLD transaction
    hold_transaction = Transaction.objects.filter(
        balance=balance, order=order, type=TransactionType.HOLD, status=TransactionStatus.PENDING
    ).first()

    if hold_transaction:
        # Update the existing HOLD transaction to PAYMENT with COMPLETED status
        hold_transaction.type = TransactionType.PAYMENT
        hold_transaction.status = TransactionStatus.COMPLETED
        hold_transaction.remaining_balance = balance.current_balance
        hold_transaction.save(update_fields=["type", "status", "remaining_balance"])
        tx = hold_transaction
    else:
        # Fallback: create new PAYMENT transaction (shouldn't happen in normal flow)
        tx = Transaction.objects.create(
            balance=balance,
            type=TransactionType.PAYMENT,
            amount=amount,
            remaining_balance=balance.current_balance,
            order=order,
            status=TransactionStatus.COMPLETED,
        )

    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])

    return WalletResult(transaction=tx, balance=balance, order=order)


@transaction.atomic
def refund_payment_by_staff(user, order_id) -> WalletResult:
    """
    Staff refunds a paid/completed order:
    - current_balance += amount
    - write REFUND transaction
    - order -> CANCELLED
    """
    order = _get_locked_order(order_id)

    if order.status not in (OrderStatus.PAID, OrderStatus.COMPLETED):
        raise WalletError("Order cannot be refunded in its current state.")

    balance = _get_locked_balance_for_user(order.user)

    amount = _quantize(order.total_amount)
    Balance.objects.filter(pk=balance.pk).update(current_balance=F("current_balance") + amount)
    balance.refresh_from_db(fields=["current_balance", "on_hold"])

    tx = Transaction.objects.create(
        balance=balance,
        type=TransactionType.REFUND,
        amount=amount,
        remaining_balance=balance.current_balance,
        order=order,
        status=TransactionStatus.COMPLETED,
    )

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status"])

    return WalletResult(transaction=tx, balance=balance, order=order)


@transaction.atomic
def cancel_order_with_hold_release(user, order_id) -> WalletResult:
    """
    Cancel an order and release held funds back to available balance.
    - on_hold -= amount (release the hold)
    - order -> CANCELLED
    - No transaction record needed
    """

    order = _get_locked_order(order_id)

    if order.user_id != user.id:
        raise WalletError("You can only cancel your own order.")

    if order.status not in (OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.CONFIRMED):
        raise WalletError("Order cannot be cancelled in its current state.")

    # Cancel deadline is 15 minutes before menu starts (when kitchen begins prep)
    now = timezone.now()
    menu_prep_deadline = order.menu.start_time - timedelta(minutes=15)

    if now > menu_prep_deadline:
        raise WalletError(
            f"Cannot cancel order. Cancellation deadline has passed. "
            f"Orders must be cancelled at least 15 minutes before the menu starts "
            f"(deadline was {menu_prep_deadline.strftime('%H:%M on %b %d')})."
        )

    balance = _get_locked_balance_for_user(order.user)
    amount = _quantize(order.total_amount)

    if order.status in (OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.CONFIRMED):
        if balance.on_hold < amount:
            raise WalletError("Insufficient held funds for this order.")

        Balance.objects.filter(pk=balance.pk).update(on_hold=F("on_hold") - amount)
        balance.refresh_from_db(fields=["current_balance", "on_hold"])

        hold_transaction = Transaction.objects.filter(
            balance=balance, order=order, type=TransactionType.HOLD, status=TransactionStatus.PENDING
        ).first()

        if hold_transaction:
            hold_transaction.status = TransactionStatus.CANCELLED
            hold_transaction.save(update_fields=["status"])

    order.status = OrderStatus.CANCELLED
    order.save(update_fields=["status"])

    return WalletResult(transaction=None, balance=balance, order=order)
