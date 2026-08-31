from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.subscription_plans import SUBSCRIPTION_PLANS
from app.routers.auth import get_current_user
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import (
    complete_payment,
    create_payment,
    get_payment_by_id,
)


router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)


@router.post(
    "/create",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_payment(
    data: PaymentCreate,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
) -> PaymentResponse:
    business_id = current_user.get("business_id")

    if not business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business ID is missing.",
        )

    plan_key = data.plan.strip().lower()
    currency = data.currency.strip().upper()

    plan = SUBSCRIPTION_PLANS.get(plan_key)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription plan.",
        )

    amount_minor = plan["prices"].get(currency)

    if amount_minor is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported currency.",
        )

    payment = await create_payment(
        business_id=business_id,
        amount_minor=amount_minor,
        currency=currency,
        plan=plan_key,
        provider="paddle",
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment could not be created.",
        )

    return PaymentResponse(**payment)

@router.post(
    "/{payment_id}/simulate-success",
    response_model=PaymentResponse,
)
async def simulate_payment_success(
    payment_id: str,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
) -> PaymentResponse:
    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )

    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    business_id = current_user.get("business_id")

    payment = await get_payment_by_id(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    if payment["business_id"] != business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    completed_payment = await complete_payment(
        payment_id=payment_id,
        provider_payment_id=f"dev_{uuid4().hex}",
    )

    if not completed_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment could not be completed.",
        )

    return PaymentResponse(**completed_payment)