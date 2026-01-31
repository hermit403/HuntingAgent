from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db, AuditResult
from models import AuditResultCreate, AuditResultResponse

router = APIRouter()


@router.post("", response_model=AuditResultResponse)
async def create_audit_result(result: AuditResultCreate, db: Session = Depends(get_db)):
    db_result = AuditResult(
        result_id=result.result_id,
        task_id=result.task_id,
        severity=result.severity.value,
        category=result.category.value,
        description=result.description,
        file_path=result.file_path,
        line_number=result.line_number,
        code_snippet=result.code_snippet
    )
    
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    return db_result


@router.get("", response_model=List[AuditResultResponse])
async def list_results(
    skip: int = 0,
    limit: int = 100,
    task_id: str = None,
    severity: str = None,
    db: Session = Depends(get_db)
):
    from database import Task

    query = db.query(AuditResult, Task.title).outerjoin(
        Task, AuditResult.task_id == Task.task_id
    )
    
    if task_id:
        query = query.filter(AuditResult.task_id == task_id)
    
    if severity:
        query = query.filter(AuditResult.severity == severity)

    query = query.order_by(AuditResult.created_at.desc())
    
    results_with_title = query.offset(skip).limit(limit).all()
    
    response = []
    for res, title in results_with_title:
        res_dict = AuditResultResponse.model_validate(res).model_dump()
        res_dict['task_title'] = title
        response.append(res_dict)
    return response


@router.get("/{result_id}", response_model=AuditResultResponse)
async def get_result(result_id: str, db: Session = Depends(get_db)):
    result = db.query(AuditResult).filter(AuditResult.result_id == result_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result
