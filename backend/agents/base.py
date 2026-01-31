import asyncio
import uuid
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import logging
from database import get_db, Message
from models import AgentMessage, MessageType


class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.status = "AFK"
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.logger = logging.getLogger(f"Agent.{agent_id}")
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        pass
    
    async def start(self):
        self.is_running = True
        self.logger.info(f"Agent {self.agent_id} started")
        asyncio.create_task(self._message_loop())
    
    async def stop(self):
        self.is_running = False
        self.logger.info(f"Agent {self.agent_id} stopped")
    
    async def _message_loop(self):
        while self.is_running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                self.status = "active"
                try:
                    from api.websocket import manager
                    asyncio.create_task(manager.send_agent_status(self.agent_id, "active"))
                except Exception as e:
                    self.logger.error(f"Failed to send status update: {e}")

                response = await self.handle_message(message)
                
                self.status = "AFK"
                try:
                    from api.websocket import manager
                    asyncio.create_task(manager.send_agent_status(self.agent_id, "AFK"))
                except Exception as e:
                    self.logger.error(f"Failed to send status update: {e}")

                if response and message.sender_id:
                    import json
                    content = json.dumps(response) if isinstance(response, dict) else str(response)
                    await self.send_message(
                        message.sender_id,
                        content,
                        MessageType.RESPONSE
                    )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in message loop: {str(e)}")
    
    async def receive_message(self, message: AgentMessage):
        await self.message_queue.put(message)
    
    async def send_message(
        self,
        receiver_id: str,
        content: str,
        message_type: MessageType
    ):
        await asyncio.sleep(2)
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id= receiver_id,
            content=content,
            message_type=message_type
        )
        
        db = next(get_db())
        try:
            db_message = Message(
                message_id=str(uuid.uuid4()),
                sender_id=message.sender_id,
                receiver_id=message.receiver_id,
                content=message.content,
                message_type=message.message_type.value,
                created_at=message.timestamp
            )
            db.add(db_message)
            db.commit()
            self.logger.info(f"Message sent to {receiver_id}")

            from core.agent_registry import agent_registry
            receiver = agent_registry.get_agent(receiver_id)
            if receiver:
                await receiver.receive_message(message)
            else:
                self.logger.warning(f"Receiver agent {receiver_id} not found in registry")
                
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    async def call_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        from tools.registry import skill_registry
        
        try:
            result = await skill_registry.execute_skill(skill_name, params)
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Skill call failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "is_running": self.is_running
        }
