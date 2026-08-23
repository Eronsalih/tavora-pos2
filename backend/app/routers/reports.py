from datetime import date, datetime, time, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database.mongodb import database
from app.routers.auth import get_current_user


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)

BUSINESS_TIMEZONE = ZoneInfo("Europe/Belgrade")


async def resolve_report_user(
    current_user: dict,
    waiter_id: str | None,
) -> dict:
    if current_user["role"] != "admin" or not waiter_id:
        return {
            "id": current_user["id"],
            "name": current_user["name"],
            "role": current_user["role"],
        }

    if not ObjectId.is_valid(waiter_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid waiter ID.",
        )

    users_collection = database["users"]

    selected_user = await users_collection.find_one(
        {
            "_id": ObjectId(waiter_id),
        }
    )

    if not selected_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waiter was not found.",
        )

    return {
        "id": str(selected_user["_id"]),
        "name": selected_user["name"],
        "role": selected_user["role"],
    }


async def calculate_daily_report(
    selected_date: date,
    target_user: dict,
) -> dict:
    start_local = datetime.combine(
        selected_date,
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    )

    end_local = datetime.combine(
        selected_date,
        time.max,
        tzinfo=BUSINESS_TIMEZONE,
    )

    start_utc = start_local.astimezone(
        timezone.utc
    )

    end_utc = end_local.astimezone(
        timezone.utc
    )

    orders_collection = database["orders"]

    query = {
        "status": "paid",
        "paid_by_user_id": target_user["id"],
        "paid_at": {
            "$gte": start_utc,
            "$lte": end_utc,
        },
    }

    orders = await orders_collection.find(
        query
    ).to_list(length=None)

    orders_count = len(orders)

    items_sold = sum(
        int(order.get("total_items", 0))
        for order in orders
    )

    cash_total = round(
        sum(
            float(order.get("total", 0))
            for order in orders
            if order.get("payment_method") == "cash"
        ),
        2,
    )

    card_total = round(
        sum(
            float(order.get("total", 0))
            for order in orders
            if order.get("payment_method") == "card"
        ),
        2,
    )

    total_sales = round(
        cash_total + card_total,
        2,
    )

    return {
        "waiter_id": target_user["id"],
        "waiter_name": target_user["name"],
        "waiter_role": target_user["role"],
        "date": selected_date.isoformat(),
        "orders_count": orders_count,
        "items_sold": items_sold,
        "cash_total": cash_total,
        "card_total": card_total,
        "total_sales": total_sales,
    }


@router.get("/daily")
async def get_daily_waiter_report(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
    report_date: date | None = Query(
        default=None,
    ),
    waiter_id: str | None = Query(
        default=None,
    ),
):
    selected_date = report_date or datetime.now(
        BUSINESS_TIMEZONE
    ).date()

    target_user = await resolve_report_user(
        current_user,
        waiter_id,
    )

    return await calculate_daily_report(
        selected_date,
        target_user,
    )


@router.get("/waiters")
async def get_report_waiters(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
):
    if current_user["role"] != "admin":
        return [
            {
                "id": current_user["id"],
                "name": current_user["name"],
                "role": current_user["role"],
            }
        ]

    users_collection = database["users"]

    waiters = await users_collection.find(
        {
            "role": "waiter",
            "is_active": {
                "$ne": False,
            },
        }
    ).sort(
        "name",
        1,
    ).to_list(
        length=None
    )

    return [
        {
            "id": str(waiter["_id"]),
            "name": waiter["name"],
            "role": waiter["role"],
        }
        for waiter in waiters
    ]


@router.post(
    "/daily/close",
    status_code=status.HTTP_201_CREATED,
)
async def close_daily_report(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
    report_date: date | None = Query(
        default=None,
    ),
    waiter_id: str | None = Query(
        default=None,
    ),
):
    selected_date = report_date or datetime.now(
        BUSINESS_TIMEZONE
    ).date()

    today = datetime.now(
        BUSINESS_TIMEZONE
    ).date()

    if selected_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A future daily report cannot be closed.",
        )

    target_user = await resolve_report_user(
        current_user,
        waiter_id,
    )

    report = await calculate_daily_report(
        selected_date,
        target_user,
    )

    daily_reports_collection = database[
        "daily_reports"
    ]

    existing_report = await daily_reports_collection.find_one(
        {
            "waiter_id": target_user["id"],
            "report_date": selected_date.isoformat(),
        }
    )

    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Daily report is already closed "
                "for this waiter and date."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    closed_report = {
        "waiter_id": target_user["id"],
        "waiter_name": target_user["name"],
        "waiter_role": target_user["role"],
        "report_date": selected_date.isoformat(),
        "orders_count": report["orders_count"],
        "items_sold": report["items_sold"],
        "cash_total": report["cash_total"],
        "card_total": report["card_total"],
        "total_sales": report["total_sales"],
        "closed_at": current_time,
        "closed_by_user_id": current_user["id"],
        "closed_by_name": current_user["name"],
        "closed_by_role": current_user["role"],
    }

    result = await daily_reports_collection.insert_one(
        closed_report
    )

    return {
        "id": str(result.inserted_id),
        "waiter_id": closed_report["waiter_id"],
        "waiter_name": closed_report["waiter_name"],
        "waiter_role": closed_report["waiter_role"],
        "report_date": closed_report["report_date"],
        "orders_count": closed_report["orders_count"],
        "items_sold": closed_report["items_sold"],
        "cash_total": closed_report["cash_total"],
        "card_total": closed_report["card_total"],
        "total_sales": closed_report["total_sales"],
        "closed_at": current_time.isoformat(),
        "closed_by_user_id": closed_report[
            "closed_by_user_id"
        ],
        "closed_by_name": closed_report[
            "closed_by_name"
        ],
        "closed_by_role": closed_report[
            "closed_by_role"
        ],
    }