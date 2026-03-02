import json
import os
import asyncio
from aiokafka import AIOKafkaConsumer
from src.kafka.topics import ORDER_CREATED
from src.database import get_database

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CONSUMER_GROUP = "orders-group"

_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


async def start_consumer():
    global _consumer, _task
    _consumer = AIOKafkaConsumer(
        ORDER_CREATED,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume_loop())
    print("✅ Kafka consumer started")


async def stop_consumer():
    global _consumer, _task
    if _task:
        _task.cancel()
    if _consumer:
        await _consumer.stop()
        print("❌ Kafka consumer stopped")


async def _consume_loop():
    async for message in _consumer:
        try:
            order_data = message.value
            db = get_database()
            await db["orders"].insert_one(order_data)
            print(f"✅ Order saved: {order_data.get('id')}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")