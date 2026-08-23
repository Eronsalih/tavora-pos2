from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import database
from app.schemas.table import TableCreate, TableUpdate
from app.services.table_seed import seed_tables


router = APIRouter(
    prefix="/api/tables",
    tags=["Tables"],
)


def serialize_table(table: dict) -> dict:
    active_order_id = table.get("active_order_id")

    return {
        "id": str(table["_id"]),
        "number": table["number"],
        "zone": table["zone"],
        "seats": table.get("seats", 4),
        "status": table.get("status", "free"),
        "is_active": table.get("is_active", True),
        "active_order_id": (
            str(active_order_id)
            if active_order_id
            else None
        ),
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_table(table: TableCreate):
    existing_table = await database.tables.find_one(
        {
            "number": table.number,
            "zone": table.zone,
        }
    )

    if existing_table:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Table {table.number} already exists "
                f"in zone {table.zone}"
            ),
        )

    table_data = table.model_dump()

    try:
        result = await database.tables.insert_one(
            table_data
        )
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table already exists",
        ) from error

    created_table = await database.tables.find_one(
        {
            "_id": result.inserted_id,
        }
    )

    return serialize_table(created_table)


@router.get("")
async def get_tables(
    zone: str | None = Query(default=None),
    table_status: str | None = Query(
        default=None,
        alias="status",
    ),
):
    filters = {}

    if zone:
        filters["zone"] = zone

    if table_status:
        filters["status"] = table_status

    tables = []

    cursor = database.tables.find(filters).sort(
        [
            ("zone", 1),
            ("number", 1),
        ]
    )

    async for table in cursor:
        tables.append(
            serialize_table(table)
        )

    return tables


@router.post("/seed")
async def seed_all_tables():
    result = await seed_tables()

    return {
        "message": "Tables seeded successfully",
        **result,
    }


@router.get("/{table_id}")
async def get_table(table_id: str):
    if not ObjectId.is_valid(table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid table ID",
        )

    table = await database.tables.find_one(
        {
            "_id": ObjectId(table_id),
        }
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    return serialize_table(table)


@router.put("/{table_id}")
async def update_table(
    table_id: str,
    table: TableUpdate,
):
    if not ObjectId.is_valid(table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid table ID",
        )

    table_object_id = ObjectId(table_id)

    existing_table = await database.tables.find_one(
        {
            "_id": table_object_id,
        }
    )

    if not existing_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    update_data = table.model_dump(
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    new_number = update_data.get(
        "number",
        existing_table["number"],
    )

    new_zone = update_data.get(
        "zone",
        existing_table["zone"],
    )

    duplicate_table = await database.tables.find_one(
        {
            "_id": {
                "$ne": table_object_id,
            },
            "number": new_number,
            "zone": new_zone,
        }
    )

    if duplicate_table:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Table {new_number} already exists "
                f"in zone {new_zone}"
            ),
        )

    await database.tables.update_one(
        {
            "_id": table_object_id,
        },
        {
            "$set": update_data,
        },
    )

    updated_table = await database.tables.find_one(
        {
            "_id": table_object_id,
        }
    )

    return serialize_table(updated_table)


@router.patch("/{table_id}/status")
async def update_table_status(
    table_id: str,
    table_status: str = Query(alias="status"),
):
    allowed_statuses = {
        "free",
        "occupied",
        "reserved",
    }

    if table_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Status must be free, occupied, or reserved"
            ),
        )

    if not ObjectId.is_valid(table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid table ID",
        )

    table_object_id = ObjectId(table_id)

    table = await database.tables.find_one(
        {
            "_id": table_object_id,
        }
    )

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    update_operation = {
        "$set": {
            "status": table_status,
        }
    }

    if table_status == "free":
        update_operation["$unset"] = {
            "active_order_id": "",
        }

    await database.tables.update_one(
        {
            "_id": table_object_id,
        },
        update_operation,
    )

    updated_table = await database.tables.find_one(
        {
            "_id": table_object_id,
        }
    )

    return serialize_table(updated_table)


@router.delete("/{table_id}")
async def delete_table(table_id: str):
    if not ObjectId.is_valid(table_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid table ID",
        )

    result = await database.tables.delete_one(
        {
            "_id": ObjectId(table_id),
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    return {
        "message": "Table deleted successfully",
    }