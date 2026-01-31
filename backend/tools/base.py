from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import resource
import signal
from contextlib import contextmanager


class BaseTool(ABC):
    def __init__(self, tool_id: str, name: str, description: str):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Tool.{tool_id}")
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return True
    
    @contextmanager
    def sandbox(self):
        def timeout_handler(signum, frame):
            raise TimeoutError("Tool execution timeout")
        old_limit = resource.getrlimit(resource.RLIMIT_AS)
        
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            try:
                import os
                if os.getenv("TOOL_RLIMIT_AS", "0") == "1":
                    max_memory = 256 * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
            except Exception as e:
                self.logger.warning(f"Failed to set memory limit: {e}")
            yield
        finally:
            signal.alarm(0)
            try:
                if old_limit:
                    resource.setrlimit(resource.RLIMIT_AS, old_limit)
            except Exception as e:
                self.logger.warning(f"Failed to restore memory limit: {e}")
