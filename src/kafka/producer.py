import json
import os
from aiokafka import AIOKafkaProducer
from src.kafka.topics import ORDER_CREATED

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

_producer: AIOKafkaProducer | None = None


async def start_producer():
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await _producer.start()
    print("✅ Kafka producer started")


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()
        print("❌ Kafka producer stopped")


async def publish_order_created(order: dict):
    if not _producer:
        raise RuntimeError("Producer not started")

    await _producer.send(ORDER_CREATED, value=order)