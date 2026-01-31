from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import re
from database import get_db, Task, AuditResult, Message, ToolExecution, Tool, Agent
from sqlalchemy import text
from core.config import settings
from models import TaskCreate, TaskResponse
from core.rate_limiter import limiter

router = APIRouter()


def validate_code_content(code: str) -> bool:
    dangerous_patterns = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
        r'compile\s*\(',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    return True

@router.post("", response_model=TaskResponse)
async def create_task(
    request: Request, 
    task: TaskCreate, 
    db: Session = Depends(get_db),
    _ = Depends(limiter.limit("10/minute"))
):
    if task.code_content and len(task.code_content) > 3000:
        raise HTTPException(status_code=400, detail="Code content exceeds 3000 characters limit")

    if task.code_content and not validate_code_content(task.code_content):
        raise HTTPException(status_code=400, detail="Code content contains dangerous functions")

    db_task = Task(
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        code_content=task.code_content,
        target_files=task.target_files,
        parameters=task.parameters,
        status="pending"
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.put("/{task_id}/status")
async def update_task_status(task_id: str, status: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = status
    
    if status == "running" and not task.started_at:
        task.started_at = datetime.now()
    elif status in ["completed", "failed"] and not task.completed_at:
        task.completed_at = datetime.now()
    
    db.commit()
    db.refresh(task)
    
    return {"status": "updated", "task_id": task_id, "new_status": status}


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    return {"status": "deleted", "task_id": task_id}


@router.post("/cleanup-db")
async def cleanup_db(db: Session = Depends(get_db)):
    deleted = {}
    try:
        deleted["audit_results"] = db.query(AuditResult).delete()
        deleted["tool_executions"] = db.query(ToolExecution).delete()
        deleted["messages"] = db.query(Message).delete()
        deleted["tasks"] = db.query(Task).delete()
        deleted["tools"] = db.query(Tool).delete()
        deleted["agents"] = db.query(Agent).delete()

        db.commit()

        if "sqlite" in settings.DATABASE_URL:
            db.execute(text("VACUUM"))

        return {"status": "cleaned", "deleted": deleted}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
