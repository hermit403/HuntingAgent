from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db, Agent
from models import AgentCreate, AgentResponse
from core.agent_registry import agent_registry

router = APIRouter()


@router.post("", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = Agent(
        agent_id=agent.agent_id,
        name=agent.name,
        role=agent.role,
        status="active"
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Retrieve agents from memory registry to get real-time status
    memory_agents = agent_registry.get_all_agents()
    response_list = []

    idx = 1
    for ag_id, agent_inst in memory_agents.items():
        response_list.append(AgentResponse(
            id=idx,
            agent_id=agent_inst.agent_id,
            name=agent_inst.name,
            role=agent_inst.role,
            status=agent_inst.get_status().get("status", "unknown")
        ))
        idx += 1
        
    return response_list


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.put("/{agent_id}/status")
async def update_agent_status(agent_id: str, status: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = status
    db.commit()
    db.refresh(agent)
    
    return {"status": "updated", "agent_id": agent_id, "new_status": status}
