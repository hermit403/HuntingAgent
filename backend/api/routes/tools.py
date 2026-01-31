from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db, Tool
from models import ToolCreate, ToolResponse

router = APIRouter()


@router.post("", response_model=ToolResponse)
async def create_tool(tool: ToolCreate, db: Session = Depends(get_db)):
    db_tool = Tool(
        tool_id=tool.tool_id,
        name=tool.name,
        description=tool.description,
        category=tool.category,
        status="active"
    )
    
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return db_tool


@router.get("", response_model=List[ToolResponse])
async def list_tools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tools = db.query(Tool).offset(skip).limit(limit).all()
    return tools


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.tool_id == tool_id).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return tool
