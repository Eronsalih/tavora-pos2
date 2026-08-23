from typing import Literal

from pydantic import BaseModel, Field


OrderStatus = Literal[
    "draft",
    "sent_to_kitchen",
    "preparing",
    "ready",
    "paid",
    "cancelled",
]


StationStatus = Literal[
    "pending",
    "preparing",
    "ready",
]


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    table_id: str
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    items: list[OrderItemCreate]


class OrderPayment(BaseModel):
    payment_method: Literal["cash", "card"]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class StationStatusUpdate(BaseModel):
    status: StationStatus


class OrderAddItems(BaseModel):
    items: list[OrderItemCreate]

class OrderTableTransfer(BaseModel):
    new_table_id: str