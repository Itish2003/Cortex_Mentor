from typing import List, Union
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected: {websocket.client}")
        else:
            logger.warning(f"Attempted to disconnect non-existent WebSocket: {websocket.client}")

    async def send_personal_message(self, message: Union[str, bytes], websocket: WebSocket):
        if isinstance(message, str):
            await websocket.send_text(message)
        else:
            await websocket.send_bytes(message)

    async def broadcast(self, message: Union[str, bytes]):
        for connection in self.active_connections:
            try:
                if isinstance(message, str):
                    await connection.send_text(message)
                else:
                    await connection.send_bytes(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket {connection.client}: {e}")
                # Optionally, handle disconnection here if send_text/send_bytes fails due to a closed connection
                # self.disconnect(connection)
