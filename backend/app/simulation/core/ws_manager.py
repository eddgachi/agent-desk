"""
WebSocket connection manager.
Maintains a set of active connections per simulation ID and
provides broadcast helpers used by the tick loop.
"""

import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self):
        # sim_id → list of active WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, sim_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(sim_id, []).append(ws)
        logger.info(
            "WS connect sim=%s total=%d", sim_id, len(self._connections[sim_id])
        )

    def disconnect(self, sim_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(sim_id, [])
        try:
            conns.remove(ws)
        except ValueError:
            pass
        logger.info("WS disconnect sim=%s remaining=%d", sim_id, len(conns))

    async def send(self, sim_id: str, message: dict) -> None:
        """Broadcast a JSON message to all clients connected to this simulation."""
        conns = self._connections.get(sim_id, [])
        if not conns:
            return

        text = json.dumps(message, default=str)
        dead: List[WebSocket] = []

        for ws in list(conns):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(sim_id, ws)

    async def broadcast_tick(self, sim_id: str, tick_data: dict) -> None:
        await self.send(sim_id, {"type": "tick_update", "data": tick_data})

    async def broadcast_event(self, sim_id: str, event_data: dict) -> None:
        await self.send(sim_id, {"type": "event", "data": event_data})

    async def broadcast_snapshot(self, sim_id: str, state_data: dict) -> None:
        await self.send(sim_id, {"type": "state_snapshot", "data": state_data})

    def has_connections(self, sim_id: str) -> bool:
        return bool(self._connections.get(sim_id))


# Singleton — imported everywhere
ws_manager = WSManager()
