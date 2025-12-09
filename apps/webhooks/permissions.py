"""
Custom permissions for webhook endpoints.
"""

import logging

from rest_framework import permissions

from apps.webhooks.services import StripeWebhookError, verify_webhook_signature

logger = logging.getLogger(__name__)


class HasValidStripeSignature(permissions.BasePermission):
    """
    Custom permission that verifies Stripe webhook signature.
    This replaces CSRF protection for webhook endpoints.
    """

    message = "Invalid Stripe signature"

    def has_permission(self, request, view):
        """
        Verify the Stripe signature from the request headers.
        Returns True if signature is valid, False otherwise.
        """
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        if not sig_header:
            logger.error("Missing Stripe signature header")
            return False

        try:
            # Verify and construct the event
            event = verify_webhook_signature(payload, sig_header)
            # Store the verified event in request for use in the view
            request.stripe_event = event
            return True
        except StripeWebhookError as e:
            logger.error(f"Stripe signature verification failed: {e}")
            return False
