"""
Payment endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.dependencies import PaymentServiceDep, CurrentUser
from app.core.exceptions import PaymentError

router = APIRouter()


class PaymentIntentRequest(BaseModel):
    """Payment intent creation request."""
    amount: int  # Amount in cents
    currency: str = "usd"


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""
    success: bool = True
    client_secret: str
    payment_intent_id: str


class StripeKeyResponse(BaseModel):
    """Stripe API key response."""
    stripe_api_key: str


@router.post("/process", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: CurrentUser,
    payment_service: PaymentServiceDep
):
    """
    Create a Stripe PaymentIntent.

    Returns client_secret for frontend to complete payment.
    Amount should be in cents (e.g., $10.00 = 1000).
    """
    try:
        result = await payment_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            metadata={"user_id": current_user.id}
        )

        return PaymentIntentResponse(
            client_secret=result["client_secret"],
            payment_intent_id=result["payment_intent_id"]
        )

    except PaymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stripeapi", response_model=StripeKeyResponse)
async def get_stripe_key(
    current_user: CurrentUser,
    payment_service: PaymentServiceDep
):
    """
    Get Stripe publishable API key.

    Used by frontend to initialize Stripe.js.
    """
    return StripeKeyResponse(
        stripe_api_key=payment_service.get_stripe_api_key()
    )
