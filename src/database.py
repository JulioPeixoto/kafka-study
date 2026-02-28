import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "orders_db")

client = None
database = None


async def connect_to_mongo():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]

    # Create indexes
    orders_collection = database["orders"]
    await orders_collection.create_index([("created_at", ASCENDING)])
    await orders_collection.create_index([("status", ASCENDING)])

    print("✅ Connected to MongoDB")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ Closed MongoDB connection")


def get_database():
    return database
