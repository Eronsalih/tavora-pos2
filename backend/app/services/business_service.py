from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.database.mongodb import database
from app.schemas.business import BusinessSignup
from app.schemas.user import UserCreate
from app.services.auth_service import (
    create_user,
    get_user_document_by_email,
)
from app.services.table_seed import seed_tables


businesses_collection = database["businesses"]
users_collection = database["users"]
tables_collection = database["tables"]


def serialize_business(
    business: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": str(business["_id"]),
        "name": business["name"],
        "owner_name": business["owner_name"],
        "email": business["email"],
        "phone": business.get("phone"),
        "country": business.get("country"),
        "is_active": business.get(
            "is_active",
            True,
        ),
        "subscription_plan": business.get(
            "subscription_plan",
            "none",
        ),
        "subscription_status": business.get(
            "subscription_status",
            "inactive",
        ),
        "subscription_started_at": business.get(
            "subscription_started_at",
        ),
        "subscription_expires_at": business.get(
            "subscription_expires_at",
        ),
        "payment_provider": business.get(
            "payment_provider",
        ),
        "created_at": business["created_at"],
        "updated_at": business["updated_at"],
    }


async def create_business_account(
    signup_data: BusinessSignup,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    normalized_email = str(
        signup_data.email,
    ).strip().lower()

    existing_user = (
        await get_user_document_by_email(
            normalized_email,
        )
    )

    if existing_user:
        raise ValueError(
            "An account with this email already exists.",
        )

    now = datetime.now(
        timezone.utc,
    )

    business_id = ObjectId()

    business_document = {
        "_id": business_id,
        "name": (
            signup_data.business_name
            .strip()
        ),
        "owner_name": (
            signup_data.owner_name
            .strip()
        ),
        "email": normalized_email,
        "phone": (
            signup_data.phone.strip()
            if signup_data.phone
            else None
        ),
        "country": (
            signup_data.country.strip()
            if signup_data.country
            else None
        ),
        "is_active": True,
        "subscription_plan": "none",
        "subscription_status": "inactive",
        "subscription_started_at": None,
        "subscription_expires_at": None,
        "payment_provider": None,
        "created_at": now,
        "updated_at": now,
    }

    await businesses_collection.insert_one(
        business_document,
    )

    admin_data = UserCreate(
        name=signup_data.owner_name,
        email=normalized_email,
        password=signup_data.password,
        pin=signup_data.pin,
        business_name=(
            signup_data.business_name
        ),
        role="admin",
    )

    created_user = None

    try:
        created_user = await create_user(
            admin_data,
            business_id=business_id,
        )

        # -----------------------------------------
        # AUTO-CREATE DEFAULT TABLES
        # -----------------------------------------
        await seed_tables(
            business_id,
        )

    except Exception:
        # Nëse diçka dështon gjatë krijimit,
        # pastrojmë të dhënat e këtij biznesi
        # që të mos mbetet account gjysmë i krijuar.

        await tables_collection.delete_many(
            {
                "business_id": business_id,
            }
        )

        await users_collection.delete_many(
            {
                "business_id": business_id,
            }
        )

        await businesses_collection.delete_one(
            {
                "_id": business_id,
            }
        )

        raise

    return (
        serialize_business(
            business_document,
        ),
        created_user,
    )


async def activate_business_subscription(
    business_id: str,
    plan: str,
    payment_provider: str,
    expires_at: datetime,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(
        business_id,
    ):
        return None

    business_object_id = ObjectId(
        business_id,
    )

    now = datetime.now(
        timezone.utc,
    )

    await businesses_collection.update_one(
        {
            "_id": business_object_id,
        },
        {
            "$set": {
                "subscription_plan": plan,
                "subscription_status": (
                    "active"
                ),
                "subscription_started_at": (
                    now
                ),
                "subscription_expires_at": (
                    expires_at
                ),
                "payment_provider": (
                    payment_provider
                ),
                "updated_at": now,
            }
        },
    )

    business = (
        await businesses_collection.find_one(
            {
                "_id": business_object_id,
            }
        )
    )

    if not business:
        return None

    return serialize_business(
        business,
    )


async def get_business_by_id(
    business_id: str,
) -> dict[str, Any] | None:
    if not ObjectId.is_valid(
        business_id,
    ):
        return None

    business = (
        await businesses_collection.find_one(
            {
                "_id": ObjectId(
                    business_id,
                ),
            }
        )
    )

    if not business:
        return None

    return serialize_business(
        business,
    )