from app.database.mongodb import database
MENU_PRODUCTS = [
    # Pizza
    {
        "name": "Margherita",
        "category": "Pizza",
        "price": 4.50,
        "available": True,
    },
    {
        "name": "Capricciosa",
        "category": "Pizza",
        "price": 5.50,
        "available": True,
    },
    {
        "name": "Pepperoni",
        "category": "Pizza",
        "price": 6.00,
        "available": True,
    },
    {
        "name": "Tuna Pizza",
        "category": "Pizza",
        "price": 6.50,
        "available": True,
    },
    {
        "name": "Chicken Pizza",
        "category": "Pizza",
        "price": 6.50,
        "available": True,
    },
    {
        "name": "Tavora Special",
        "category": "Pizza",
        "price": 7.50,
        "available": True,
    },

    # Pije
    {
        "name": "Coca Cola",
        "category": "Pije",
        "price": 1.50,
        "available": True,
    },
    {
        "name": "Fanta",
        "category": "Pije",
        "price": 1.50,
        "available": True,
    },
    {
        "name": "Sprite",
        "category": "Pije",
        "price": 1.50,
        "available": True,
    },
    {
        "name": "Ice Tea",
        "category": "Pije",
        "price": 1.50,
        "available": True,
    },
    {
        "name": "Orange Juice",
        "category": "Pije",
        "price": 2.00,
        "available": True,
    },
    {
        "name": "Ujë Mineral",
        "category": "Pije",
        "price": 1.00,
        "available": True,
    },

    # Akullore
    {
        "name": "Vanilla Ice Cream",
        "category": "Akullore",
        "price": 2.00,
        "available": True,
    },
    {
        "name": "Chocolate Ice Cream",
        "category": "Akullore",
        "price": 2.00,
        "available": True,
    },
    {
        "name": "Strawberry Ice Cream",
        "category": "Akullore",
        "price": 2.00,
        "available": True,
    },
    {
        "name": "Mixed Ice Cream",
        "category": "Akullore",
        "price": 2.50,
        "available": True,
    },

    # Deserte
    {
        "name": "Cheesecake",
        "category": "Deserte",
        "price": 3.00,
        "available": True,
    },
    {
        "name": "Chocolate Cake",
        "category": "Deserte",
        "price": 3.00,
        "available": True,
    },
    {
        "name": "Tiramisu",
        "category": "Deserte",
        "price": 3.50,
        "available": True,
    },
    {
        "name": "Fruit Salad",
        "category": "Deserte",
        "price": 3.50,
        "available": True,
    },
]

async def seed_products():
    products_collection = database["products"]

    created = 0
    skipped = 0

    for product in MENU_PRODUCTS:
        existing_product = await products_collection.find_one(
            {
                "name": product["name"],
                "category": product["category"],
            }
        )

        if existing_product:
            skipped += 1
            continue

        await products_collection.insert_one(product)
        created += 1

    return {
        "created": created,
        "skipped": skipped,
        "total": len(MENU_PRODUCTS),
    }