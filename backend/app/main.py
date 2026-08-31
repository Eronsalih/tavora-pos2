from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    health,
    orders,
    payments,
    platform_admin,
    products,
    reports,
    tables,
)


app = FastAPI(
    title="Tavora POS API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health.router
)

app.include_router(
    products.router
)

app.include_router(
    tables.router
)

app.include_router(
    orders.router
)

app.include_router(
    auth.router
)

app.include_router(
    reports.router
)

app.include_router(
    payments.router
)

app.include_router(
    platform_admin.router
)