from datetime import datetime, timezone

from bson import ObjectId
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.mongodb import database
from app.schemas.order import (
    OrderAddItems,
    OrderCreate,
    OrderPayment,
    OrderStatusUpdate,
    OrderTableTransfer,
    OrderUpdate,
    StationStatusUpdate,
)
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
)


ORDER_STATUS_TRANSITIONS = {
    "draft": {
        "sent_to_kitchen",
        "paid",
        "cancelled",
    },
    "sent_to_kitchen": {
        "preparing",
        "paid",
        "cancelled",
    },
    "preparing": {
        "ready",
        "paid",
    },
    "ready": {
        "paid",
    },
    "paid": set(),
    "cancelled": set(),
}


ACTIVE_ORDER_STATUSES = {
    "draft",
    "sent_to_kitchen",
    "preparing",
    "ready",
}


PAYABLE_ORDER_STATUSES = {
    "draft",
    "sent_to_kitchen",
    "preparing",
    "ready",
}


CANCELLABLE_ORDER_STATUSES = {
    "draft",
    "sent_to_kitchen",
}


KITCHEN_CATEGORIES = {
    "Breakfast",
    "Soups",
    "Salads",
    "Appetizers",
    "Main Dishes",
    "Grill",
    "Pasta",
    "Pizza",
    "Sandwiches",
    "Traditional Food",
    "Side Dishes",
    "Desserts",
}


BAR_CATEGORIES = {
    "Hot Drinks",
    "Cold Drinks",
    "Alcohol",
    "Cocktails",
}


def serialize_datetime(value):
    if value is None:
        return None

    if not hasattr(value, "isoformat"):
        return value

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.isoformat()


def serialize_order(order: dict) -> dict:
    return {
        "id": str(order["_id"]),
        "table_id": str(order["table_id"]),
        "table_number": order["table_number"],
        "table_zone": order["table_zone"],
        "opened_by_user_id": order.get("opened_by_user_id"),
        "opened_by_name": order.get("opened_by_name"),
        "opened_by_role": order.get("opened_by_role"),
        "items": order.get("items", []),
        "total_items": order.get("total_items", 0),
        "total": order.get("total", 0),
        "status": order.get("status", "draft"),
        "kitchen_status": order.get("kitchen_status"),
        "bar_status": order.get("bar_status"),
        "payment_method": order.get("payment_method"),
        "paid_by_user_id": order.get("paid_by_user_id"),
        "paid_by_name": order.get("paid_by_name"),
        "paid_by_role": order.get("paid_by_role"),
        "stock_deducted": order.get(
            "stock_deducted",
            False,
        ),
        "stock_restored": order.get(
            "stock_restored",
            False,
        ),
        "created_at": serialize_datetime(
            order.get("created_at")
        ),
        "updated_at": serialize_datetime(
            order.get("updated_at")
        ),
        "sent_to_kitchen_at": serialize_datetime(
            order.get("sent_to_kitchen_at")
        ),
        "preparing_at": serialize_datetime(
            order.get("preparing_at")
        ),
        "ready_at": serialize_datetime(
            order.get("ready_at")
        ),
        "paid_at": serialize_datetime(
            order.get("paid_at")
        ),
        "cancelled_at": serialize_datetime(
            order.get("cancelled_at")
        ),
        "stock_deducted_at": serialize_datetime(
            order.get("stock_deducted_at")
        ),
        "stock_restored_at": serialize_datetime(
            order.get("stock_restored_at")
        ),
    }


async def prepare_order_items(
    items,
) -> tuple[list, int, float]:
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one product.",
        )

    products_collection = database["products"]

    prepared_items = []
    total_items = 0
    order_total = 0.0

    for item in items:
        if not ObjectId.is_valid(item.product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product ID: {item.product_id}",
            )

        product = await products_collection.find_one(
            {
                "_id": ObjectId(item.product_id),
                "is_active": {
                    "$ne": False,
                },
            }
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {item.product_id}",
            )

        product_price = float(product["price"])

        subtotal = round(
            product_price * item.quantity,
            2,
        )

        prepared_items.append(
            {
                "product_id": str(product["_id"]),
                "name": product["name"],
                "category": product.get(
                    "category",
                    "Other",
                ),
                "price": product_price,
                "quantity": item.quantity,
                "subtotal": subtotal,
            }
        )

        total_items += item.quantity
        order_total += subtotal

    return (
        prepared_items,
        total_items,
        round(order_total, 2),
    )


def order_has_kitchen_items(order: dict) -> bool:
    return any(
        item.get("category") in KITCHEN_CATEGORIES
        for item in order.get("items", [])
    )


def order_has_bar_items(order: dict) -> bool:
    return any(
        item.get("category") in BAR_CATEGORIES
        for item in order.get("items", [])
    )


def filter_items_by_categories(
    order: dict,
    categories: set[str],
) -> dict:
    filtered_items = [
        item
        for item in order.get("items", [])
        if item.get("category") in categories
    ]

    serialized = serialize_order(order)

    serialized["items"] = filtered_items
    serialized["total_items"] = sum(
        int(item.get("quantity", 0))
        for item in filtered_items
    )

    return serialized


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    order_data: OrderCreate,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
):
    if not ObjectId.is_valid(order_data.table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid table ID.",
        )

    tables_collection = database["tables"]
    orders_collection = database["orders"]

    table_object_id = ObjectId(
        order_data.table_id
    )

    table = await tables_collection.find_one(
        {
            "_id": table_object_id,
        }
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found.",
        )

    active_order_id = table.get(
        "active_order_id"
    )

    if active_order_id:
        existing_order = (
            await orders_collection.find_one(
                {
                    "_id": active_order_id,
                    "status": {
                        "$in": list(
                            ACTIVE_ORDER_STATUSES
                        ),
                    },
                }
            )
        )

        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This table already has an active order. "
                    "Update the existing order."
                ),
            )

        await tables_collection.update_one(
            {
                "_id": table_object_id,
            },
            {
                "$unset": {
                    "active_order_id": "",
                }
            },
        )

    (
        prepared_items,
        total_items,
        order_total,
    ) = await prepare_order_items(
        order_data.items
    )

    current_time = datetime.now(
        timezone.utc
    )

    new_order = {
        "table_id": table_object_id,
        "table_number": table["number"],
        "table_zone": table["zone"],
        "opened_by_user_id": current_user["id"],
        "opened_by_name": current_user["name"],
        "opened_by_role": current_user["role"],
        "items": prepared_items,
        "total_items": total_items,
        "total": order_total,
        "status": "draft",
        "kitchen_status": None,
        "bar_status": None,
        "payment_method": None,
        "stock_deducted": False,
        "stock_restored": False,
        "created_at": current_time,
        "updated_at": current_time,
        "sent_to_kitchen_at": None,
        "preparing_at": None,
        "ready_at": None,
        "paid_at": None,
        "cancelled_at": None,
        "stock_deducted_at": None,
        "stock_restored_at": None,
    }

    result = await orders_collection.insert_one(
        new_order
    )

    await tables_collection.update_one(
        {
            "_id": table_object_id,
        },
        {
            "$set": {
                "status": "occupied",
                "active_order_id": result.inserted_id,
            }
        },
    )

    created_order = (
        await orders_collection.find_one(
            {
                "_id": result.inserted_id,
            }
        )
    )

    return serialize_order(created_order)


@router.get("")
async def get_orders():
    orders = []

    cursor = (
        database["orders"]
        .find()
        .sort(
            "created_at",
            -1,
        )
    )

    async for order in cursor:
        orders.append(
            serialize_order(order)
        )

    return orders


@router.get("/kitchen")
async def get_kitchen_orders():
    kitchen_orders = []

    cursor = (
        database["orders"]
        .find(
            {
    "status": {
        "$nin": [
            "paid",
            "cancelled",
        ]
    },
    "kitchen_status": {
        "$in": [
            "pending",
            "preparing",
            "ready",
        ]
    },
}
        )
        .sort(
            "created_at",
            1,
        )
    )

    async for order in cursor:
        kitchen_items = [
            item
            for item in order.get("items", [])
            if item.get("category")
            in KITCHEN_CATEGORIES
        ]

        if not kitchen_items:
            continue

        kitchen_orders.append(
            filter_items_by_categories(
                order,
                KITCHEN_CATEGORIES,
            )
        )

    return kitchen_orders


@router.get("/bar")
async def get_bar_orders():
    bar_orders = []

    cursor = (
        database["orders"]
        .find(
            {
    "status": {
        "$nin": [
            "paid",
            "cancelled",
        ]
    },
    "bar_status": {
        "$in": [
            "pending",
            "preparing",
            "ready",
        ]
    },
}
        )
        .sort(
            "created_at",
            1,
        )
    )

    async for order in cursor:
        bar_items = [
            item
            for item in order.get("items", [])
            if item.get("category")
            in BAR_CATEGORIES
        ]

        if not bar_items:
            continue

        bar_orders.append(
            filter_items_by_categories(
                order,
                BAR_CATEGORIES,
            )
        )

    return bar_orders


@router.delete("/reset-demo")
async def reset_demo_orders():
    orders_collection = database["orders"]
    tables_collection = database["tables"]

    delete_result = (
        await orders_collection.delete_many({})
    )

    table_update_result = (
        await tables_collection.update_many(
            {},
            {
                "$set": {
                    "status": "free",
                },
                "$unset": {
                    "active_order_id": "",
                },
            },
        )
    )

    return {
        "message": (
            "Demo orders were reset successfully."
        ),
        "deleted_orders": (
            delete_result.deleted_count
        ),
        "updated_tables": (
            table_update_result.modified_count
        ),
    }
async def update_overall_order_status_if_ready(
    order_object_id: ObjectId,
):
    orders_collection = database["orders"]

    order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    if not order:
        return

    kitchen_status = order.get("kitchen_status")
    bar_status = order.get("bar_status")

    has_kitchen = kitchen_status is not None
    has_bar = bar_status is not None

    kitchen_ready = (
        not has_kitchen
        or kitchen_status == "ready"
    )

    bar_ready = (
        not has_bar
        or bar_status == "ready"
    )

    has_any_station = has_kitchen or has_bar

    if (
        has_any_station
        and kitchen_ready
        and bar_ready
    ):
        current_time = datetime.now(
            timezone.utc
        )

        await orders_collection.update_one(
            {
                "_id": order_object_id,
            },
            {
                "$set": {
                    "status": "ready",
                    "ready_at": current_time,
                    "updated_at": current_time,
                }
            },
        )

@router.patch("/{order_id}/kitchen-status")
async def update_kitchen_status(
    order_id: str,
    status_data: StationStatusUpdate,
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]

    existing_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if existing_order.get("status") in {
        "paid",
        "cancelled",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed orders cannot be updated.",
        )

    if not order_has_kitchen_items(
        existing_order
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Order does not contain kitchen items."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": {
                "kitchen_status": status_data.status,
                "updated_at": current_time,
            }
        },
    )

    await update_overall_order_status_if_ready(
        order_object_id
    )

    updated_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    return serialize_order(updated_order)


@router.patch("/{order_id}/bar-status")
async def update_bar_status(
    order_id: str,
    status_data: StationStatusUpdate,
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]

    existing_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if existing_order.get("status") in {
        "paid",
        "cancelled",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed orders cannot be updated.",
        )

    if not order_has_bar_items(
        existing_order
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Order does not contain bar items."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": {
                "bar_status": status_data.status,
                "updated_at": current_time,
            }
        },
    )

    await update_overall_order_status_if_ready(
        order_object_id
    )

    updated_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    return serialize_order(updated_order)


@router.patch("/{order_id}/transfer-table")
async def transfer_order_table(
    order_id: str,
    transfer_data: OrderTableTransfer,
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    if not ObjectId.is_valid(transfer_data.new_table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target table ID.",
        )

    order_object_id = ObjectId(order_id)
    new_table_object_id = ObjectId(transfer_data.new_table_id)

    orders_collection = database["orders"]
    tables_collection = database["tables"]

    existing_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if existing_order.get("status") not in ACTIVE_ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active orders can be transferred.",
        )

    old_table_id = existing_order.get("table_id")

    if old_table_id == new_table_object_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The order is already assigned to this table.",
        )

    new_table = await tables_collection.find_one(
        {
            "_id": new_table_object_id,
        }
    )

    if not new_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target table not found.",
        )

    if new_table.get("is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target table is not active.",
        )

    if new_table.get("status") != "free":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target table is not free.",
        )

    if new_table.get("active_order_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target table already has an active order.",
        )

    current_time = datetime.now(timezone.utc)

    target_result = await tables_collection.update_one(
        {
            "_id": new_table_object_id,
            "status": "free",
            "$or": [
                {"active_order_id": {"$exists": False}},
                {"active_order_id": None},
            ],
        },
        {
            "$set": {
                "status": "occupied",
                "active_order_id": order_object_id,
            }
        },
    )

    if target_result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Target table is no longer available.",
        )

    try:
        await orders_collection.update_one(
            {
                "_id": order_object_id,
            },
            {
                "$set": {
                    "table_id": new_table_object_id,
                    "table_number": new_table["number"],
                    "table_zone": new_table["zone"],
                    "updated_at": current_time,
                }
            },
        )

        await tables_collection.update_one(
            {
                "_id": old_table_id,
                "active_order_id": order_object_id,
            },
            {
                "$set": {
                    "status": "free",
                },
                "$unset": {
                    "active_order_id": "",
                },
            },
        )

    except Exception:
        await tables_collection.update_one(
            {
                "_id": new_table_object_id,
                "active_order_id": order_object_id,
            },
            {
                "$set": {
                    "status": "free",
                },
                "$unset": {
                    "active_order_id": "",
                },
            },
        )

        raise

    updated_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    return serialize_order(updated_order)

@router.get("/{order_id}")
async def get_order(order_id: str):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order = await database[
        "orders"
    ].find_one(
        {
            "_id": ObjectId(order_id),
        }
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return serialize_order(order)

@router.post("/{order_id}/add-items")
async def add_items_to_order(
    order_id: str,
    order_data: OrderAddItems,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]
    products_collection = database["products"]

    existing_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if existing_order.get("status") in {
        "draft",
        "paid",
        "cancelled",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Items can only be added to an active "
                "sent order."
            ),
        )

    (
    prepared_items,
    added_total_items,
    added_total,
) = await prepare_order_items(
        order_data.items
)

    current_time = datetime.now(
        timezone.utc
    )
    
    for item in prepared_items:
        item["added_by_user_id"] = current_user["id"]
        item["added_by_name"] = current_user["name"]
        item["added_by_role"] = current_user["role"]
        item["added_at"] = current_time
    


    # Kontrollo stock-un para se ta ndryshojmë.
    for item in prepared_items:
        product_id = item["product_id"]
        quantity = int(item["quantity"])

        if not ObjectId.is_valid(product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID.",
            )

        product = await products_collection.find_one(
            {
                "_id": ObjectId(product_id),
            }
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {product_id}",
            )

        current_stock = int(
            product.get("stock", 0)
        )

        if current_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Not enough stock for "
                    f"{product.get('name', 'product')}. "
                    f"Available: {current_stock}."
                ),
            )

    # Zbrit vetëm stock-un e produkteve të reja.
    for item in prepared_items:
        await products_collection.update_one(
            {
                "_id": ObjectId(
                    item["product_id"]
                ),
            },
            {
                "$inc": {
                    "stock": -int(
                        item["quantity"]
                    ),
                }
            },
        )

    current_time = datetime.now(
        timezone.utc
    )

    existing_items = existing_order.get(
        "items",
        [],
    )

    updated_items = [
        *existing_items,
        *prepared_items,
    ]

    updated_total_items = (
        int(
            existing_order.get(
                "total_items",
                0,
            )
        )
        + added_total_items
    )

    updated_total = round(
        float(
            existing_order.get(
                "total",
                0,
            )
        )
        + added_total,
        2,
    )

    update_fields = {
        "items": updated_items,
        "total_items": updated_total_items,
        "total": updated_total,
        "updated_at": current_time,
        "stock_deducted": True,
    }

    added_kitchen_items = any(
        item.get("category")
        in KITCHEN_CATEGORIES
        for item in prepared_items
    )

    added_bar_items = any(
        item.get("category")
        in BAR_CATEGORIES
        for item in prepared_items
    )

    if added_kitchen_items:
        update_fields[
            "kitchen_status"
        ] = "pending"

    if added_bar_items:
        update_fields[
            "bar_status"
        ] = "pending"

    # Porosia nuk është më komplet ready
    # nëse sapo erdhën produkte të reja.
    if added_kitchen_items or added_bar_items:
        update_fields["status"] = (
            "sent_to_kitchen"
        )

        update_fields["ready_at"] = None

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": update_fields,
        },
    )

    updated_order = await orders_collection.find_one(
        {
            "_id": order_object_id,
        }
    )

    return serialize_order(updated_order)

@router.put("/{order_id}")
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]
    tables_collection = database["tables"]

    existing_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if (
        existing_order.get("status")
        != "draft"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only draft orders can be updated."
            ),
        )

    (
        prepared_items,
        total_items,
        order_total,
    ) = await prepare_order_items(
        order_data.items
    )

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": {
                "items": prepared_items,
                "total_items": total_items,
                "total": order_total,
                "updated_at": datetime.now(
                    timezone.utc
                ),
            }
        },
    )

    await tables_collection.update_one(
        {
            "_id": existing_order[
                "table_id"
            ],
        },
        {
            "$set": {
                "status": "occupied",
                "active_order_id": (
                    order_object_id
                ),
            }
        },
    )

    updated_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    return serialize_order(updated_order)


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]
    products_collection = database["products"]

    existing_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    current_status = existing_order.get(
        "status",
        "draft",
    )

    new_status = status_data.status

    if current_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Order already has status "
                f"'{new_status}'."
            ),
        )

    allowed_statuses = (
        ORDER_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Status cannot change from "
                f"'{current_status}' "
                f"to '{new_status}'."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    update_fields = {
        "status": new_status,
        "updated_at": current_time,
    }

    status_timestamp_fields = {
        "sent_to_kitchen": (
            "sent_to_kitchen_at"
        ),
        "preparing": "preparing_at",
        "ready": "ready_at",
    }

    timestamp_field = (
        status_timestamp_fields.get(
            new_status
        )
    )

    if timestamp_field:
        update_fields[
            timestamp_field
        ] = current_time

    if (
        current_status == "draft"
        and new_status == "sent_to_kitchen"
    ):
        for item in existing_order.get(
            "items",
            [],
        ):
            product_id = item.get(
                "product_id"
            )

            quantity = int(
                item.get(
                    "quantity",
                    0,
                )
            )

            if (
                not product_id
                or not ObjectId.is_valid(
                    product_id
                )
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Order contains an invalid "
                        "product ID."
                    ),
                )

            if quantity <= 0:
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Order contains an invalid "
                        "quantity."
                    ),
                )

            product = (
                await products_collection.find_one(
                    {
                        "_id": ObjectId(
                            product_id
                        ),
                    }
                )
            )

            if not product:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail=(
                        f"Product not found: "
                        f"{product_id}"
                    ),
                )

            current_stock = int(
                product.get(
                    "stock",
                    0,
                )
            )

            if current_stock < quantity:
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        f"Not enough stock for "
                        f"{product.get('name', 'product')}. "
                        f"Available: {current_stock}, "
                        f"requested: {quantity}."
                    ),
                )

        for item in existing_order.get(
            "items",
            [],
        ):
            await products_collection.update_one(
                {
                    "_id": ObjectId(
                        item["product_id"]
                    ),
                },
                {
                    "$inc": {
                        "stock": -int(
                            item["quantity"]
                        ),
                    },
                },
            )

        update_fields[
            "stock_deducted"
        ] = True

        update_fields[
            "stock_restored"
        ] = False

        update_fields[
            "stock_deducted_at"
        ] = current_time

        if order_has_kitchen_items(
            existing_order
        ):
            update_fields[
                "kitchen_status"
            ] = "pending"
        else:
            update_fields[
                "kitchen_status"
            ] = None

        if order_has_bar_items(
            existing_order
        ):
            update_fields[
                "bar_status"
            ] = "pending"
        else:
            update_fields[
                "bar_status"
            ] = None

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": update_fields,
        },
    )

    updated_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    return serialize_order(updated_order)


@router.patch("/{order_id}/pay")
async def pay_order(
    order_id: str,
    payment_data: OrderPayment,
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]
    tables_collection = database["tables"]

    existing_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    current_status = existing_order.get(
        "status",
        "draft",
    )

    if current_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order is already paid.",
        )

    if current_status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cancelled orders cannot be paid."
            ),
        )

    if (
        current_status
        not in PAYABLE_ORDER_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This order cannot be paid "
                "in its current status."
            ),
        )

    if existing_order.get(
        "total",
        0,
    ) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Order total must be greater than zero."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
        "$set": {
            "status": "paid",
            "payment_method": (
                payment_data.payment_method
            ),
            "paid_by_user_id": current_user["id"],
            "paid_by_name": current_user["name"],
            "paid_by_role": current_user["role"],
            "paid_at": current_time,
            "updated_at": current_time,
}
        },
    )

    await tables_collection.update_one(
        {
            "_id": existing_order[
                "table_id"
            ],
        },
        {
            "$set": {
                "status": "free",
            },
            "$unset": {
                "active_order_id": "",
            },
        },
    )

    paid_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    return serialize_order(paid_order)


@router.patch("/{order_id}/cancel")
async def cancel_order(order_id: str):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID.",
        )

    order_object_id = ObjectId(order_id)

    orders_collection = database["orders"]
    tables_collection = database["tables"]
    products_collection = database["products"]

    existing_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    if not existing_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    current_status = existing_order.get(
        "status",
        "draft",
    )

    if current_status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Order is already cancelled."
            ),
        )

    if current_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Paid orders cannot be cancelled."
            ),
        )

    if (
        current_status
        not in CANCELLABLE_ORDER_STATUSES
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only draft or sent-to-kitchen "
                "orders can be cancelled."
            ),
        )

    current_time = datetime.now(
        timezone.utc
    )

    stock_was_deducted = (
        existing_order.get(
            "stock_deducted",
            False,
        )
    )

    stock_already_restored = (
        existing_order.get(
            "stock_restored",
            False,
        )
    )

    should_restore_stock = (
        stock_was_deducted
        and not stock_already_restored
    )

    if should_restore_stock:
        for item in existing_order.get(
            "items",
            [],
        ):
            product_id = item.get(
                "product_id"
            )

            quantity = int(
                item.get(
                    "quantity",
                    0,
                )
            )

            if (
                not product_id
                or not ObjectId.is_valid(
                    product_id
                )
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Order contains an invalid "
                        "product ID."
                    ),
                )

            if quantity <= 0:
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Order contains an invalid "
                        "quantity."
                    ),
                )

            await products_collection.update_one(
                {
                    "_id": ObjectId(
                        product_id
                    ),
                },
                {
                    "$inc": {
                        "stock": quantity,
                    },
                },
            )

    update_fields = {
        "status": "cancelled",
        "payment_method": None,
        "cancelled_at": current_time,
        "updated_at": current_time,
        "kitchen_status": None,
        "bar_status": None,
    }

    if should_restore_stock:
        update_fields[
            "stock_restored"
        ] = True

        update_fields[
            "stock_restored_at"
        ] = current_time

    await orders_collection.update_one(
        {
            "_id": order_object_id,
        },
        {
            "$set": update_fields,
        },
    )

    await tables_collection.update_one(
        {
            "_id": existing_order[
                "table_id"
            ],
        },
        {
            "$set": {
                "status": "free",
            },
            "$unset": {
                "active_order_id": "",
            },
        },
    )

    cancelled_order = (
        await orders_collection.find_one(
            {
                "_id": order_object_id,
            }
        )
    )

    return serialize_order(
        cancelled_order
    )