from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._instance.agents = {}
        return cls._instance
    
    def register_agent(self, agent_id: str, agent: Any):
        self.agents[agent_id] = agent
        logger.info(f"Agent registered: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Any]:
        return self.agents

agent_registry = AgentRegistry()
