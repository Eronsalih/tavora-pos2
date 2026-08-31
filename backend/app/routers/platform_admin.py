import re
from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.database.mongodb import database
from app.routers.auth import get_current_user


router = APIRouter(
    prefix="/api/platform-admin",
    tags=["Platform Admin"],
)


# =========================================================
# COLLECTIONS
# =========================================================


businesses_collection = database[
    "businesses"
]

users_collection = database[
    "users"
]

payments_collection = database[
    "payments"
]

products_collection = database[
    "products"
]

tables_collection = database[
    "tables"
]

orders_collection = database[
    "orders"
]


# =========================================================
# SUPERADMIN GUARD
# =========================================================


async def require_superadmin(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
) -> dict:
    if current_user.get(
        "role"
    ) != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Tavora owner access is required."
            ),
        )

    return current_user


# =========================================================
# HELPERS
# =========================================================


def serialize_datetime(
    value,
):
    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    return str(value)


def serialize_business(
    business: dict,
) -> dict:
    return {
        "id": str(
            business["_id"]
        ),
        "name": business.get(
            "name",
            "",
        ),
        "owner_name": business.get(
            "owner_name",
            "",
        ),
        "email": business.get(
            "email",
            "",
        ),
        "phone": business.get(
            "phone"
        ),
        "country": business.get(
            "country"
        ),
        "is_active": business.get(
            "is_active",
            True,
        ),
        "subscription_plan": (
            business.get(
                "subscription_plan",
                "none",
            )
        ),
        "subscription_status": (
            business.get(
                "subscription_status",
                "inactive",
            )
        ),
        "subscription_started_at": (
            serialize_datetime(
                business.get(
                    "subscription_started_at"
                )
            )
        ),
        "subscription_expires_at": (
            serialize_datetime(
                business.get(
                    "subscription_expires_at"
                )
            )
        ),
        "payment_provider": (
            business.get(
                "payment_provider"
            )
        ),
        "created_at": (
            serialize_datetime(
                business.get(
                    "created_at"
                )
            )
        ),
        "updated_at": (
            serialize_datetime(
                business.get(
                    "updated_at"
                )
            )
        ),
    }


def serialize_payment(
    payment: dict,
    business_name: str | None = None,
) -> dict:
    amount_minor = int(
        payment.get(
            "amount_minor",
            0,
        )
        or 0
    )

    return {
        "id": str(
            payment["_id"]
        ),
        "business_id": str(
            payment.get(
                "business_id"
            )
        ),
        "business_name": (
            business_name
        ),
        "amount_minor": (
            amount_minor
        ),
        "currency": payment.get(
            "currency"
        ),
        "plan": payment.get(
            "plan"
        ),
        "provider": payment.get(
            "provider"
        ),
        "provider_payment_id": (
            payment.get(
                "provider_payment_id"
            )
        ),
        "status": payment.get(
            "status"
        ),
        "created_at": (
            serialize_datetime(
                payment.get(
                    "created_at"
                )
            )
        ),
        "updated_at": (
            serialize_datetime(
                payment.get(
                    "updated_at"
                )
            )
        ),
        "paid_at": (
            serialize_datetime(
                payment.get(
                    "paid_at"
                )
            )
        ),
    }


async def get_business_name(
    business_id,
) -> str | None:
    if isinstance(
        business_id,
        ObjectId,
    ):
        business_object_id = (
            business_id
        )

    elif ObjectId.is_valid(
        str(business_id)
    ):
        business_object_id = ObjectId(
            str(business_id)
        )

    else:
        return None

    business = await businesses_collection.find_one(
        {
            "_id": business_object_id,
        },
        {
            "name": 1,
        },
    )

    if not business:
        return None

    return business.get(
        "name"
    )


# =========================================================
# DASHBOARD
# =========================================================


@router.get(
    "/dashboard"
)
async def get_platform_dashboard(
    _: Annotated[
        dict,
        Depends(require_superadmin),
    ],
):
    now = datetime.now(
        timezone.utc
    )

    month_start = datetime(
        year=now.year,
        month=now.month,
        day=1,
        tzinfo=timezone.utc,
    )

    total_businesses = (
        await businesses_collection.count_documents(
            {}
        )
    )

    enabled_businesses = (
        await businesses_collection.count_documents(
            {
                "is_active": {
                    "$ne": False,
                }
            }
        )
    )

    disabled_businesses = (
        await businesses_collection.count_documents(
            {
                "is_active": False,
            }
        )
    )

    active_subscriptions = (
        await businesses_collection.count_documents(
            {
                "subscription_status": (
                    "active"
                ),
                "subscription_expires_at": {
                    "$gt": now,
                },
            }
        )
    )

    inactive_subscriptions = (
        total_businesses
        - active_subscriptions
    )

    paid_payments = (
        await payments_collection.count_documents(
            {
                "status": "paid",
            }
        )
    )

    pending_payments = (
        await payments_collection.count_documents(
            {
                "status": "pending",
            }
        )
    )

    # -----------------------------------------------------
    # TOTAL REVENUE BY CURRENCY
    # -----------------------------------------------------

    revenue_pipeline = [
        {
            "$match": {
                "status": "paid",
            }
        },
        {
            "$group": {
                "_id": "$currency",
                "total_minor": {
                    "$sum": "$amount_minor",
                },
                "payments_count": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "_id": 1,
            }
        },
    ]

    total_revenue_by_currency = []

    async for result in payments_collection.aggregate(
        revenue_pipeline
    ):
        total_revenue_by_currency.append(
            {
                "currency": result.get(
                    "_id"
                ),
                "total_minor": int(
                    result.get(
                        "total_minor",
                        0,
                    )
                ),
                "payments_count": (
                    result.get(
                        "payments_count",
                        0,
                    )
                ),
            }
        )

    # -----------------------------------------------------
    # CURRENT MONTH REVENUE
    # -----------------------------------------------------

    monthly_revenue_pipeline = [
        {
            "$match": {
                "status": "paid",
                "paid_at": {
                    "$gte": month_start,
                },
            }
        },
        {
            "$group": {
                "_id": "$currency",
                "total_minor": {
                    "$sum": "$amount_minor",
                },
                "payments_count": {
                    "$sum": 1,
                },
            }
        },
        {
            "$sort": {
                "_id": 1,
            }
        },
    ]

    monthly_revenue_by_currency = []

    async for result in payments_collection.aggregate(
        monthly_revenue_pipeline
    ):
        monthly_revenue_by_currency.append(
            {
                "currency": result.get(
                    "_id"
                ),
                "total_minor": int(
                    result.get(
                        "total_minor",
                        0,
                    )
                ),
                "payments_count": (
                    result.get(
                        "payments_count",
                        0,
                    )
                ),
            }
        )

    return {
        "total_businesses": (
            total_businesses
        ),
        "enabled_businesses": (
            enabled_businesses
        ),
        "disabled_businesses": (
            disabled_businesses
        ),
        "active_subscriptions": (
            active_subscriptions
        ),
        "inactive_subscriptions": (
            inactive_subscriptions
        ),
        "paid_payments": (
            paid_payments
        ),
        "pending_payments": (
            pending_payments
        ),
        "total_revenue_by_currency": (
            total_revenue_by_currency
        ),
        "monthly_revenue_by_currency": (
            monthly_revenue_by_currency
        ),
    }


# =========================================================
# BUSINESSES LIST
# =========================================================


@router.get(
    "/businesses"
)
async def get_platform_businesses(
    _: Annotated[
        dict,
        Depends(require_superadmin),
    ],
    search: str | None = Query(
        default=None,
    ),
    subscription_status: str | None = Query(
        default=None,
    ),
):
    query: dict = {}

    if subscription_status:
        query[
            "subscription_status"
        ] = subscription_status

    if search and search.strip():
        safe_search = re.escape(
            search.strip()
        )

        query["$or"] = [
            {
                "name": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
            {
                "owner_name": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
            {
                "email": {
                    "$regex": safe_search,
                    "$options": "i",
                }
            },
        ]

    businesses = []

    cursor = businesses_collection.find(
        query
    ).sort(
        "created_at",
        -1,
    )

    async for business in cursor:
        business_id = business[
            "_id"
        ]

        business_data = (
            serialize_business(
                business
            )
        )

        business_data[
            "users_count"
        ] = await users_collection.count_documents(
            {
                "business_id": (
                    business_id
                ),
            }
        )

        latest_payment = (
            await payments_collection.find_one(
                {
                    "business_id": (
                        business_id
                    ),
                },
                sort=[
                    (
                        "created_at",
                        -1,
                    )
                ],
            )
        )

        if latest_payment:
            business_data[
                "latest_payment"
            ] = serialize_payment(
                latest_payment,
                business_name=business.get(
                    "name"
                ),
            )

        else:
            business_data[
                "latest_payment"
            ] = None

        businesses.append(
            business_data
        )

    return businesses


# =========================================================
# BUSINESS DETAILS
# =========================================================


@router.get(
    "/businesses/{business_id}"
)
async def get_platform_business(
    business_id: str,
    _: Annotated[
        dict,
        Depends(require_superadmin),
    ],
):
    if not ObjectId.is_valid(
        business_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Invalid business ID."
            ),
        )

    business_object_id = ObjectId(
        business_id
    )

    business = (
        await businesses_collection.find_one(
            {
                "_id": business_object_id,
            }
        )
    )

    if not business:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Business was not found."
            ),
        )

    business_data = (
        serialize_business(
            business
        )
    )

    business_data["counts"] = {
        "users": (
            await users_collection.count_documents(
                {
                    "business_id": (
                        business_object_id
                    ),
                }
            )
        ),
        "products": (
            await products_collection.count_documents(
                {
                    "business_id": (
                        business_object_id
                    ),
                }
            )
        ),
        "tables": (
            await tables_collection.count_documents(
                {
                    "business_id": (
                        business_object_id
                    ),
                }
            )
        ),
        "orders": (
            await orders_collection.count_documents(
                {
                    "business_id": (
                        business_object_id
                    ),
                }
            )
        ),
    }

    recent_payments = []

    payment_cursor = (
        payments_collection.find(
            {
                "business_id": (
                    business_object_id
                ),
            }
        )
        .sort(
            "created_at",
            -1,
        )
        .limit(
            10
        )
    )

    async for payment in payment_cursor:
        recent_payments.append(
            serialize_payment(
                payment,
                business_name=business.get(
                    "name"
                ),
            )
        )

    business_data[
        "recent_payments"
    ] = recent_payments

    return business_data


# =========================================================
# SUBSCRIPTIONS
# =========================================================


@router.get(
    "/subscriptions"
)
async def get_platform_subscriptions(
    _: Annotated[
        dict,
        Depends(require_superadmin),
    ],
    subscription_status: str | None = Query(
        default=None,
        alias="status",
    ),
):
    query: dict = {}

    if subscription_status:
        query[
            "subscription_status"
        ] = subscription_status

    subscriptions = []

    cursor = businesses_collection.find(
        query
    ).sort(
        "created_at",
        -1,
    )

    async for business in cursor:
        subscriptions.append(
            {
                "business_id": str(
                    business["_id"]
                ),
                "business_name": (
                    business.get(
                        "name"
                    )
                ),
                "owner_name": (
                    business.get(
                        "owner_name"
                    )
                ),
                "email": business.get(
                    "email"
                ),
                "plan": business.get(
                    "subscription_plan",
                    "none",
                ),
                "status": business.get(
                    "subscription_status",
                    "inactive",
                ),
                "started_at": (
                    serialize_datetime(
                        business.get(
                            "subscription_started_at"
                        )
                    )
                ),
                "expires_at": (
                    serialize_datetime(
                        business.get(
                            "subscription_expires_at"
                        )
                    )
                ),
                "payment_provider": (
                    business.get(
                        "payment_provider"
                    )
                ),
            }
        )

    return subscriptions


# =========================================================
# PAYMENTS
# =========================================================


@router.get(
    "/payments"
)
async def get_platform_payments(
    _: Annotated[
        dict,
        Depends(require_superadmin),
    ],
    payment_status: str | None = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
):
    query: dict = {}

    if payment_status:
        query[
            "status"
        ] = payment_status

    payments = []

    cursor = (
        payments_collection.find(
            query
        )
        .sort(
            "created_at",
            -1,
        )
        .limit(
            limit
        )
    )

    async for payment in cursor:
        business_name = (
            await get_business_name(
                payment.get(
                    "business_id"
                )
            )
        )

        payments.append(
            serialize_payment(
                payment,
                business_name=business_name,
            )
        )

    return payments