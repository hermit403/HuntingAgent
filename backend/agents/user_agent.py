from typing import Dict, Any, Optional
from agents.base import BaseAgent
from models import AgentMessage, MessageType


class UserAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="user_agent",
            name="User Interaction Agent",
            role="Directly interact with frontend, handle user requests"
        )
        self.pending_tasks = []
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        self.pending_tasks.append(task)
        import json
        await self.send_message(
            "coordinator_agent",
            json.dumps(task),
            MessageType.TASK
        )
        return {
            "status": "accepted",
            "task_id": task_id,
            "message": "Task forwarded to coordinator"
        }
    
    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        if message.message_type == MessageType.TASK:
            self.logger.info(f"Received task message: {message.content}")
            import json
            if isinstance(message.content, dict):
                return await self.process_task(message.content)
            elif isinstance(message.content, str):
                try:
                    task_data = json.loads(message.content)
                    return await self.process_task(task_data)
                except json.JSONDecodeError:
                    return await self.process_task({"task_id": "current", "code_content": message.content})
            return await self.process_task({"task_id": "current", "code_content": message.content})
        
        if message.message_type == MessageType.RESPONSE:
            self.logger.info(f"Received response: {message.content}")
            return None
        
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        for task in self.pending_tasks:
            if task.get("task_id") == task_id:
                return task
        return None
