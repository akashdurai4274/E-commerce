"""
Payment service.
Handles Stripe payment processing.
"""
from typing import Optional
import stripe

from app.core.config import settings
from app.core.exceptions import PaymentError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    """
    Payment processing service using Stripe.

    Handles:
    - Payment intent creation
    - Payment confirmation
    - Refunds

    Design Notes:
    - Uses Stripe Payment Intents API for SCA compliance
    - All amounts are in cents (smallest currency unit)
    """

    def __init__(self):
        """Initialize payment service."""
        if not settings.STRIPE_SECRET_KEY:
            logger.warning("Stripe secret key not configured")

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Create a Stripe PaymentIntent.

        Args:
            amount: Amount in cents
            currency: Currency code
            metadata: Additional metadata

        Returns:
            Dict with client_secret and payment_intent_id

        Raises:
            PaymentError: If Stripe request fails
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )

            logger.info(
                "Payment intent created",
                intent_id=intent.id,
                amount=amount
            )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }

        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error creating payment intent",
                error=str(e)
            )
            raise PaymentError(f"Payment processing failed: {str(e)}")

    async def get_payment_intent(self, payment_intent_id: str) -> dict:
        """
        Retrieve a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            PaymentIntent details
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency
            }

        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error retrieving payment intent",
                intent_id=payment_intent_id,
                error=str(e)
            )
            raise PaymentError(f"Failed to retrieve payment: {str(e)}")

    async def confirm_payment(self, payment_intent_id: str) -> dict:
        """
        Confirm a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            Confirmation result
        """
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)

            logger.info(
                "Payment confirmed",
                intent_id=intent.id,
                status=intent.status
            )

            return {
                "id": intent.id,
                "status": intent.status,
                "success": intent.status == "succeeded"
            }

        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error confirming payment",
                intent_id=payment_intent_id,
                error=str(e)
            )
            raise PaymentError(f"Payment confirmation failed: {str(e)}")

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> dict:
        """
        Create a refund.

        Args:
            payment_intent_id: Original PaymentIntent ID
            amount: Amount to refund (None for full refund)
            reason: Reason for refund

        Returns:
            Refund details
        """
        try:
            refund_params = {"payment_intent": payment_intent_id}

            if amount:
                refund_params["amount"] = amount

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(
                "Refund created",
                refund_id=refund.id,
                amount=refund.amount
            )

            return {
                "id": refund.id,
                "amount": refund.amount,
                "status": refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error creating refund",
                intent_id=payment_intent_id,
                error=str(e)
            )
            raise PaymentError(f"Refund failed: {str(e)}")

    def get_stripe_api_key(self) -> str:
        """
        Get publishable Stripe API key for frontend.

        Returns:
            Stripe publishable key
        """
        return settings.STRIPE_PUBLISHABLE_KEY
