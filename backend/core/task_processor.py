import logging
import asyncio
from datetime import datetime
from database import get_db, Task
from models import AgentMessage, MessageType
from agents.user_agent import UserAgent

logger = logging.getLogger(__name__)

class TaskProcessor:
    def __init__(self):
        self.running = False
        self.user_agent = None
        
    async def start(self):
        self.running = True
        from core.agent_registry import agent_registry
        self.user_agent = agent_registry.get_agent("user_agent")
        
        if not self.user_agent:
            logger.warning("UserAgent not found in registry, creating new one (fallback)")
            self.user_agent = UserAgent()
            await self.user_agent.start()
            
        logger.info("Task processor started")
        
        asyncio.create_task(self._process_pending_tasks())
        
    async def stop(self):
        self.running = False
        logger.info("Task processor stopped")
        
    async def _process_pending_tasks(self):
        while self.running:
            try:
                await asyncio.sleep(5)
                await self._check_and_process_tasks()
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(10)
                
    async def _check_and_process_tasks(self):
        from sqlalchemy.orm import Session
        import json
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            pending_tasks = db.query(Task).filter(
                Task.status == "pending",
                Task.started_at == None
            ).all()
            
            for task in pending_tasks:
                try:
                    logger.info(f"Processing pending task: {task.task_id}")
                    
                    task_data = {
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "code_content": task.code_content,
                        "target_files": task.target_files,
                        "parameters": task.parameters
                    }
                    
                    await self.user_agent.send_message(
                        "user_agent",
                        json.dumps(task_data),
                        MessageType.TASK
                    )
                    
                    task.started_at = datetime.now()
                    task.status = "running"
                    db.commit()
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing task {task.task_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking pending tasks: {e}")
        finally:
            db.close()

task_processor = TaskProcessor()
