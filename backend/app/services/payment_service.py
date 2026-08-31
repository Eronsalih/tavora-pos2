from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument

from app.core.subscription_plans import SUBSCRIPTION_PLANS
from app.database.mongodb import database
from app.services.business_service import (
    activate_business_subscription,
)


payments_collection = database["payments"]


def serialize_payment(
    payment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(payment["_id"]),
        "business_id": str(payment["business_id"]),
        "amount_minor": payment["amount_minor"],
        "currency": payment["currency"],
        "plan": payment["plan"],
        "provider": payment["provider"],
        "provider_payment_id": payment.get(
            "provider_payment_id"
        ),
        "status": payment["status"],
        "created_at": payment["created_at"],
        "updated_at": payment["updated_at"],
        "paid_at": payment.get("paid_at"),
    }


async def create_payment(
    business_id: str,
    amount_minor: int,
    currency: str,
    plan: str,
    provider: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(business_id):
        return None

    now = datetime.now(timezone.utc)

    payment_document = {
        "business_id": ObjectId(business_id),
        "amount_minor": amount_minor,
        "currency": currency,
        "plan": plan,
        "provider": provider,
        "provider_payment_id": None,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "paid_at": None,
    }

    result = await payments_collection.insert_one(
        payment_document
    )

    payment = await payments_collection.find_one(
        {
            "_id": result.inserted_id,
        }
    )

    if not payment:
        return None

    return serialize_payment(payment)


async def complete_payment(
    payment_id: str,
    provider_payment_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(payment_id):
        return None

    payment = await payments_collection.find_one(
        {
            "_id": ObjectId(payment_id),
        }
    )

    if not payment:
        return None

    # Payment already completed.
    # Allow the same provider payment ID to be retried safely.
    if payment["status"] == "paid":
        if (
            payment.get("provider_payment_id")
            == provider_payment_id
        ):
            return serialize_payment(payment)

        return None

    if payment["status"] != "pending":
        return None

    plan = SUBSCRIPTION_PLANS.get(
        payment["plan"]
    )

    if not plan:
        return None

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        days=plan["duration_days"]
    )

    # First activate the business subscription.
    business = await activate_business_subscription(
        business_id=str(payment["business_id"]),
        plan=payment["plan"],
        payment_provider=payment["provider"],
        expires_at=expires_at,
    )

    if not business:
        return None

    # Mark payment as paid only after
    # subscription activation succeeded.
    updated_payment = (
        await payments_collection.find_one_and_update(
            {
                "_id": ObjectId(payment_id),
                "status": "pending",
            },
            {
                "$set": {
                    "status": "paid",
                    "provider_payment_id": (
                        provider_payment_id
                    ),
                    "paid_at": now,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    )

    if not updated_payment:
        return None

    return serialize_payment(
        updated_payment
    )


async def get_payment_by_id(
    payment_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(payment_id):
        return None

    payment = await payments_collection.find_one(
        {
            "_id": ObjectId(payment_id),
        }
    )

    if not payment:
        return None

    return serialize_payment(payment)