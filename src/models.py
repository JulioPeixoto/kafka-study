from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from bson import ObjectId


class OrderBase(SQLModel):
    customer_name: str
    total_amount: float
    status: str = "pending"
    description: Optional[str] = None


class Order(OrderBase):
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(SQLModel):
    customer_name: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None
