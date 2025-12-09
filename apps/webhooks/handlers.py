import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.wallets.models import Balance, Transaction
from apps.webhooks.models import WebhookEvent, WebhookStatus

logger = logging.getLogger(__name__)


class StripeWebhookError(Exception):
    pass


class StripeWebhookHandler:
    """
    Handler class for processing Stripe webhook events.
    Manages event processing with idempotency and proper error handling.
    """

    def __init__(self, request):
        self.request = request
        self.event = getattr(request, "stripe_event", None)

        if not self.event:
            raise ValueError("Request does not contain a verified Stripe event")

    def handle_event(self):
        """
        Process the webhook event with idempotency.
        Creates or retrieves WebhookEvent record and delegates to appropriate handler.
        """
        event_id = self.event["id"]
        event_type = self.event["type"]

        logger.info(f"Handling Stripe webhook event: {event_type} ({event_id})")

        # Process with idempotency
        webhook_event = self._get_or_create_webhook_event(event_id, event_type)

        if webhook_event.status == WebhookStatus.COMPLETED:
            logger.info(f"Event {event_id} already processed, skipping")
            return webhook_event

        # Mark as processing
        webhook_event.status = WebhookStatus.PROCESSING
        webhook_event.save(update_fields=["status", "updated_at"])

        try:
            # Route to appropriate handler
            if event_type == "checkout.session.completed":
                self._handle_checkout_session_completed()
            else:
                logger.warning(f"Unhandled event type: {event_type}")

            # Mark as completed
            webhook_event.status = WebhookStatus.COMPLETED
            webhook_event.processed_at = timezone.now()
            webhook_event.error_message = None
            webhook_event.save(update_fields=["status", "processed_at", "error_message", "updated_at"])

            logger.info(f"Successfully processed webhook event {event_id}")

        except Exception as e:
            # Mark as failed
            webhook_event.status = WebhookStatus.FAILED
            webhook_event.error_message = str(e)
            webhook_event.save(update_fields=["status", "error_message", "updated_at"])
            logger.error(f"Failed to process webhook event {event_id}: {e}", exc_info=True)
            raise

        return webhook_event

    def _get_or_create_webhook_event(self, event_id: str, event_type: str) -> WebhookEvent:
        """
        Get or create a WebhookEvent record for idempotency.
        """
        webhook_event, created = WebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "event_type": event_type,
                "source": "stripe",
                "payload": self.event,
                "status": WebhookStatus.PENDING,
            },
        )

        if not created:
            logger.info(f"Webhook event {event_id} already exists with status {webhook_event.status}")

        return webhook_event

    @transaction.atomic
    def _handle_checkout_session_completed(self):
        """
        Handle the checkout.session.completed event.
        Credits the user's balance and updates the transaction status.
        """
        session = self.event["data"]["object"]
        session_id = session["id"]
        payment_intent_id = session.get("payment_intent")

        logger.info(f"Processing checkout.session.completed: {session_id}")

        # Find the pending transaction
        try:
            tx = Transaction.objects.select_for_update().get(
                stripe_checkout_session_id=session_id,
            )
        except Transaction.DoesNotExist as e:
            logger.error(f"Transaction not found for session {session_id}")
            raise StripeWebhookError(f"Transaction not found for session {session_id}") from e

        # Check if already processed (idempotency)
        if tx.status == "completed":
            logger.info(f"Transaction {tx.id} already completed, skipping")
            return

        # Update transaction with payment intent ID
        tx.stripe_payment_intent_id = payment_intent_id
        tx.status = "completed"
        tx.save(update_fields=["stripe_payment_intent_id", "status", "updated_at"])

        # Credit the user's balance atomically
        balance = Balance.objects.select_for_update().get(pk=tx.balance_id)
        Balance.objects.filter(pk=balance.pk).update(current_balance=F("current_balance") + tx.amount)
        balance.refresh_from_db()

        # Update remaining_balance to reflect the new balance
        tx.remaining_balance = balance.current_balance
        tx.save(update_fields=["remaining_balance", "updated_at"])

        logger.info(
            f"Successfully credited {tx.amount} to user {balance.user_id}. New balance: {balance.current_balance}"
        )
