from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from datetime import datetime
from typing import List
from bson import ObjectId

from src.models import Order, OrderCreate, OrderUpdate
from src.database import connect_to_mongo, close_mongo_connection, get_database
from src.kafka.producer import start_producer, stop_producer, publish_order_created
from src.kafka.consumer import start_consumer, stop_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await start_producer()
    await start_consumer()
    yield
    await stop_consumer()
    await stop_producer()
    await close_mongo_connection()


app = FastAPI(title="Order CRUD API", version="1.0.0", lifespan=lifespan)


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API is running"}


@app.post("/orders", status_code=status.HTTP_202_ACCEPTED, tags=["Orders"])
async def create_order(order: OrderCreate):
    """Publish order to Kafka — consumer persists to MongoDB"""
    order_dict = order.model_dump()
    order_dict["id"] = str(ObjectId())
    order_dict["created_at"] = datetime.utcnow().isoformat()
    order_dict["updated_at"] = datetime.utcnow().isoformat()

    await publish_order_created(order_dict)

    return {"status": "accepted", "id": order_dict["id"]}


@app.get("/orders", response_model=List[Order], tags=["Orders"])
async def list_orders(skip: int = 0, limit: int = 10) -> List[Order]:
    db = get_database()
    orders = []
    async for order in db["orders"].find().skip(skip).limit(limit):
        order["id"] = str(order.pop("_id"))
        orders.append(Order(**order))
    return orders


@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def get_order(order_id: str) -> Order:
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format"
        )

    order = await db["orders"].find_one({"_id": ObjectId(order_id)})

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    order["id"] = str(order.pop("_id"))
    return Order(**order)


@app.put("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def update_order(order_id: str, order_update: OrderUpdate) -> Order:
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format"
        )

    update_data = order_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = await db["orders"].find_one_and_update(
        {"_id": ObjectId(order_id)}, {"$set": update_data}, return_document=True
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    result["id"] = str(result.pop("_id"))
    return Order(**result)


@app.delete(
    "/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Orders"]
)
async def delete_order(order_id: str):
    db = get_database()

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format"
        )

    result = await db["orders"].delete_one({"_id": ObjectId(order_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return None
