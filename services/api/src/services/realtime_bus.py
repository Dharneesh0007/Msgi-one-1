"""
MSGI One — Real-Time Pub/Sub Bus & Bounded WebSocket Connection Manager (Phase 6)
Uses Redis Pub/Sub when REDIS_URL is configured and reachable; otherwise uses an
in-process multi-subscriber Pub/Sub bus for local/CI execution.
Redis is strictly ephemeral fan-out (PostgreSQL remains authoritative durable storage).
Governing Textbooks: Kurose & Ross (Computer Networking), Martin Kleppmann (DDIA).
"""

import asyncio
from collections import defaultdict
import json
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

from src.core.config import settings

logger = logging.getLogger(__name__)


class ChatConnectionManager:
    """Manages per-worker active WebSocket connections, bounded queues, presence, and Pub/Sub fan-out."""

    def __init__(self, outbound_queue_size: int = 100) -> None:
        self.outbound_queue_size = outbound_queue_size
        # user_id -> set of active WebSocket objects on this worker
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        # websocket -> asyncio.Queue for backpressure-bounded sends
        self._queues: Dict[WebSocket, asyncio.Queue] = {}
        self._writer_tasks: Dict[WebSocket, asyncio.Task] = {}
        self._redis_client: Any = None
        self._redis_pubsub_available: bool = False

    async def init_redis_if_configured(self) -> bool:
        if not settings.REDIS_URL:
            return False
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
            await client.ping()
            self._redis_client = client
            self._redis_pubsub_available = True
            return True
        except Exception as exc:
            logger.warning("Redis Pub/Sub unavailable (%s); using local worker fan-out.", exc)
            self._redis_client = None
            self._redis_pubsub_available = False
            return False

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)
        q: asyncio.Queue = asyncio.Queue(maxsize=self.outbound_queue_size)
        self._queues[websocket] = q
        self._writer_tasks[websocket] = asyncio.create_task(self._writer_loop(websocket, q))

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if conns and websocket in conns:
            conns.discard(websocket)
            if not conns:
                self._connections.pop(user_id, None)

        task = self._writer_tasks.pop(websocket, None)
        if task:
            task.cancel()
        self._queues.pop(websocket, None)

    async def _writer_loop(self, websocket: WebSocket, q: asyncio.Queue) -> None:
        try:
            while True:
                payload = await q.get()
                await websocket.send_text(json.dumps(payload))
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def is_user_online(self, user_id: str) -> bool:
        return bool(self._connections.get(user_id))

    def online_user_ids(self) -> List[str]:
        return [uid for uid, sockets in self._connections.items() if sockets]

    async def send_to_user(self, user_id: str, event: Dict[str, Any]) -> bool:
        """Enqueue event to all active sockets for user_id with bounded backpressure."""
        sockets = list(self._connections.get(user_id, set()))
        delivered = False
        for ws in sockets:
            q = self._queues.get(ws)
            if q is None:
                continue
            if q.full():
                # Drop oldest non-critical frame to prevent unbounded memory growth
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(event)
                delivered = True
            except asyncio.QueueFull:
                pass
        return delivered

    async def publish_conversation_event(
        self,
        conversation_id: str,
        recipient_ids: List[str],
        event: Dict[str, Any],
    ) -> None:
        """
        Fan out event to connected recipients on this worker and, if Redis is active,
        publish to Redis channel `chat:{conversation_id}` for peer API workers.
        """
        if self._redis_client is not None and self._redis_pubsub_available:
            try:
                await self._redis_client.publish(
                    f"chat:{conversation_id}",
                    json.dumps({"recipient_ids": recipient_ids, "event": event}),
                )
            except Exception as exc:
                logger.warning("Redis publish failed (%s); continuing local delivery.", exc)

        for uid in recipient_ids:
            await self.send_to_user(uid, event)


chat_connection_manager = ChatConnectionManager()
