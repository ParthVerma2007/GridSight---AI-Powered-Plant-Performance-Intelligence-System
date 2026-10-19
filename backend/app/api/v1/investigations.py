from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.investigation import Investigation
from app.auth.rbac import get_current_role, require_role, UserRole

router = APIRouter(prefix="/investigations", tags=["Investigations"])

class InvestigationCreate(BaseModel):
    plant_id: str = "helios-50"
    title: str
    cause_category: str
    cause_id: Optional[str] = None
    description: Optional[str] = None
    owner: str
    priority: str = "medium"
    controllability: str = "controllable"
    recurrence_flag: bool = False
    deadline: Optional[datetime] = None
    action_plan: Optional[str] = None

class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[datetime] = None
    action_plan: Optional[str] = None
    resolution_notes: Optional[str] = None

@router.get("/list", response_model=List[dict])
def list_investigations(
    plant_id: str = "helios-50",
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    query = db.query(Investigation).filter(Investigation.plant_id == plant_id)
    if status:
        query = query.filter(Investigation.status == status)
    invs = query.order_by(Investigation.created_at.desc()).all()

    return [{
        "id": i.id,
        "plant_id": i.plant_id,
        "cause_id": i.cause_id,
        "title": i.title,
        "cause_category": i.cause_category,
        "description": i.description,
        "owner": i.owner,
        "status": i.status,
        "priority": i.priority,
        "controllability": i.controllability,
        "recurrence_flag": i.recurrence_flag,
        "deadline": i.deadline.isoformat() if i.deadline else None,
        "action_plan": i.action_plan,
        "resolution_notes": i.resolution_notes,
        "created_at": i.created_at.isoformat(),
        "updated_at": i.updated_at.isoformat() if i.updated_at else None
    } for i in invs]

@router.post("/create", response_model=dict)
def create_investigation(
    data: InvestigationCreate,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.OPERATIONS, UserRole.ADMIN, UserRole.CEO]))
):
    inv = Investigation(
        plant_id=data.plant_id,
        title=data.title,
        cause_category=data.cause_category,
        cause_id=data.cause_id,
        description=data.description,
        owner=data.owner,
        status="open",
        priority=data.priority,
        controllability=data.controllability,
        recurrence_flag=data.recurrence_flag,
        deadline=data.deadline,
        action_plan=data.action_plan
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    return {"message": "Investigation created successfully", "id": inv.id}

@router.patch("/{id}/update", response_model=dict)
def update_investigation(
    id: int,
    data: InvestigationUpdate,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.OPERATIONS, UserRole.ADMIN, UserRole.CEO]))
):
    inv = db.query(Investigation).filter(Investigation.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if data.title is not None:
        inv.title = data.title
    if data.owner is not None:
        inv.owner = data.owner
    if data.status is not None:
        inv.status = data.status
    if data.priority is not None:
        inv.priority = data.priority
    if data.deadline is not None:
        inv.deadline = data.deadline
    if data.action_plan is not None:
        inv.action_plan = data.action_plan
    if data.resolution_notes is not None:
        inv.resolution_notes = data.resolution_notes

    inv.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Investigation updated successfully", "id": inv.id}
