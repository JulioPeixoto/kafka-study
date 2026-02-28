from fastapi import FastAPI, HTTPException, status
from datetime import datetime
from typing import List
from bson import ObjectId

from src.models import Order, OrderCreate, OrderUpdate
from src.database import connect_to_mongo, close_mongo_connection, get_database

app = FastAPI(title="Order CRUD API", version="1.0.0")


@app.on_event("startup")
async def startup():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API is running"}


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(order: OrderCreate) -> Order:
    """Create a new order"""
    db = get_database()
    order_dict = order.model_dump()
    order_dict["_id"] = str(ObjectId())
    order_dict["created_at"] = datetime.utcnow()
    order_dict["updated_at"] = datetime.utcnow()

    result = await db["orders"].insert_one(order_dict)

    order_dict["id"] = str(result.inserted_id)
    return Order(**order_dict)


@app.get("/orders", response_model=List[Order], tags=["Orders"])
async def list_orders(skip: int = 0, limit: int = 10) -> List[Order]:
    """List all orders with pagination"""
    db = get_database()
    orders = []

    async for order in db["orders"].find().skip(skip).limit(limit):
        order["id"] = str(order.pop("_id"))
        orders.append(Order(**order))

    return orders


@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def get_order(order_id: str) -> Order:
    """Get a specific order by ID"""
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )

    order = await db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order["id"] = str(order.pop("_id"))
    return Order(**order)


@app.put("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def update_order(order_id: str, order_update: OrderUpdate) -> Order:
    """Update an existing order"""
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )

    update_data = order_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    result = await db["orders"].find_one_and_update(
        {"_id": ObjectId(order_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    result["id"] = str(result.pop("_id"))
    return Order(**result)


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Orders"])
async def delete_order(order_id: str):
    """Delete an order"""
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )

    result = await db["orders"].delete_one({"_id": ObjectId(order_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return None
