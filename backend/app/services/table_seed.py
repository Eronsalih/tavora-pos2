from app.database.mongodb import database


async def seed_tables() -> dict[str, int]:
    tables_to_create = []

    # Salla: tavolinat 1 - 10
    for number in range(1, 11):
        tables_to_create.append(
            {
                "number": number,
                "zone": "Salla",
                "seats": 4,
                "status": "free",
                "is_active": True,
            }
        )

    # Terrace: tavolinat 11 - 100
    for number in range(11, 101):
        tables_to_create.append(
            {
                "number": number,
                "zone": "Terrace",
                "seats": 4,
                "status": "free",
                "is_active": True,
            }
        )

    # VIP: tavolinat 1 - 4
    for number in range(1, 5):
        tables_to_create.append(
            {
                "number": number,
                "zone": "VIP",
                "seats": 12,
                "status": "free",
                "is_active": True,
            }
        )

    created_count = 0
    skipped_count = 0

    for table in tables_to_create:
        existing_table = await database.tables.find_one(
            {
                "number": table["number"],
                "zone": table["zone"],
            }
        )

        if existing_table:
            skipped_count += 1
            continue

        await database.tables.insert_one(table)
        created_count += 1

    return {
        "created": created_count,
        "skipped": skipped_count,
        "total": len(tables_to_create),
    }