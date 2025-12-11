import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeWebhookError(Exception):
    pass


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """
    Verify the Stripe webhook signature and return the event.

    Args:
        payload: Raw request body as bytes
        sig_header: Stripe-Signature header value

    Returns:
        dict: Verified Stripe event

    Raises:
        StripeWebhookError: If verification fails
    """
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        return event
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise StripeWebhookError("Invalid payload") from e
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise StripeWebhookError("Invalid signature") from e
