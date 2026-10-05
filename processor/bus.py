"""
SentinelAI Unified Message Broker Client
Integrates Redpanda (Kafka API) with transparent fallback to internal asyncio event bus.
"""
import os
import json
import asyncio
import logging
from typing import Callable, List, Dict, Any, Optional

logger = logging.getLogger("SentinelBus")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", "sentinel-node")

class InternalBus:
    """High-speed asynchronous in-memory event bus for local dev, evaluation & fallback."""
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, message: Dict[str, Any]):
        async with self._lock:
            queues = list(self._subscribers.get(topic, []))
            wildcard_queues = list(self._subscribers.get("*", []))
        
        all_queues = queues + wildcard_queues
        for q in all_queues:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, topic: str) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=10000)
        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(q)
        return q

    async def unsubscribe(self, topic: str, q: asyncio.Queue):
        async with self._lock:
            if topic in self._subscribers and q in self._subscribers[topic]:
                self._subscribers[topic].remove(q)

_internal_bus = InternalBus()

class SentinelBus:
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP, client_id: str = CLIENT_ID):
        self.bootstrap = bootstrap_servers
        self.client_id = client_id
        self.is_kafka = False
        self.producer = None
        self._active_consumers = []

    async def start_producer(self):
        # Quick pre-flight socket check to avoid spawning lingering background connection loops
        host, port = "localhost", 9092
        if ":" in self.bootstrap:
            parts = self.bootstrap.split(":")
            host, port = parts[0], int(parts[1])
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=0.25
            )
            writer.close()
            await writer.wait_closed()
        except Exception:
            self.is_kafka = False
            self.producer = None
            logger.info(f"[SentinelBus] Redpanda/Kafka unavailable at {self.bootstrap}. Operating with high-speed internal event bus.")
            return

        try:
            from aiokafka import AIOKafkaProducer
            producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=1000
            )
            await asyncio.wait_for(producer.start(), timeout=1.0)
            self.producer = producer
            self.is_kafka = True
            logger.info(f"[SentinelBus] Connected to Redpanda/Kafka producer at {self.bootstrap}")
        except Exception as e:
            self.is_kafka = False
            self.producer = None
            logger.info(f"[SentinelBus] Kafka unavailable ({e}). Using internal event bus.")

    async def publish(self, topic: str, message: Dict[str, Any]):
        # Always publish to internal bus so local listeners (e.g. WebSocket, eval harness) receive it
        await _internal_bus.publish(topic, message)

        if self.is_kafka and self.producer:
            try:
                await self.producer.send_and_wait(topic, message)
            except Exception as e:
                logger.warning(f"[SentinelBus] Kafka publish failed ({e}), internal bus retained.")

    async def subscribe(self, topics: List[str], handler: Callable[[str, Dict[str, Any]], Any]):
        """Starts a background loop consuming messages from specified topics."""
        # Subscribe to internal bus for each topic
        for t in topics:
            asyncio.create_task(self._internal_consume_loop(t, handler))

        # Also attempt Kafka consumer if Kafka is active
        if self.is_kafka:
            try:
                from aiokafka import AIOKafkaConsumer
                consumer = AIOKafkaConsumer(
                    *topics,
                    bootstrap_servers=self.bootstrap,
                    group_id=f"{self.client_id}-group",
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset="latest"
                )
                await consumer.start()
                self._active_consumers.append(consumer)
                asyncio.create_task(self._kafka_consume_loop(consumer, handler))
                logger.info(f"[SentinelBus] Kafka consumer started for topics: {topics}")
            except Exception as e:
                logger.warning(f"[SentinelBus] Failed to start Kafka consumer: {e}")

    async def _internal_consume_loop(self, topic: str, handler: Callable[[str, Dict[str, Any]], Any]):
        q = await _internal_bus.subscribe(topic)
        try:
            while True:
                msg = await q.get()
                try:
                    res = handler(topic, msg)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as ex:
                    logger.error(f"[SentinelBus] Error handling internal message on {topic}: {ex}")
                finally:
                    q.task_done()
        except asyncio.CancelledError:
            await _internal_bus.unsubscribe(topic, q)

    async def _kafka_consume_loop(self, consumer, handler: Callable[[str, Dict[str, Any]], Any]):
        try:
            async for record in consumer:
                try:
                    res = handler(record.topic, record.value)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as ex:
                    logger.error(f"[SentinelBus] Error handling Kafka message: {ex}")
        except asyncio.CancelledError:
            await consumer.stop()

    async def close(self):
        if self.producer and self.is_kafka:
            await self.producer.stop()
        for c in self._active_consumers:
            await c.stop()

# Global bus instance
bus = SentinelBus()
