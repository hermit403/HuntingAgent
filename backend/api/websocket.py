from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)
    
    async def send_task_update(self, task_id: str, status: str, progress: float = 0.0, message: str = None):
        payload = {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
            "progress": progress
        }
        if message:
            payload["message"] = message
        await self.broadcast(payload)
    
    async def send_agent_status(self, agent_id: str, status: str):
        message = {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status
        }
        await self.broadcast(message)
    
    async def send_audit_result(self, task_id: str, result: dict):
        message = {
            "type": "audit_result",
            "task_id": task_id,
            "result": result
        }
        await self.broadcast(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe_task":
                task_id = message.get("task_id")
                logger.info(f"Client {client_id} subscribed to task {task_id}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)
