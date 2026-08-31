from datetime import datetime

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    plan: str
    currency: str


class PaymentResponse(BaseModel):
    id: str
    business_id: str
    amount_minor: int
    currency: str
    plan: str
    provider: str
    provider_payment_id: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None