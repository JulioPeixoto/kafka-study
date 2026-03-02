from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    customer_name: str
    total_amount: float
    status: str = "pending"
    description: Optional[str] = None


class Order(OrderBase):
    id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None
