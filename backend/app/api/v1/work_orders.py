import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.work_order import WorkOrder
from app.models.plant import Asset
from app.auth.rbac import get_current_role, require_role, UserRole

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

class WorkOrderCreate(BaseModel):
    plant_id: str = "helios-50"
    asset_id: str
    title: str
    description: Optional[str] = None
    priority: str = "P2_HIGH"
    assigned_technician: str = "Carlos Mendez"
    estimated_hours: float = 2.5
    procedure_code: str = "SOP-INV-02"

class WorkOrderUpdate(BaseModel):
    status: Optional[str] = None
    assigned_technician: Optional[str] = None
    actual_hours: Optional[float] = None
    safety_interlock_verified: Optional[bool] = None
    loto_applied: Optional[bool] = None

@router.get("/list", response_model=List[dict])
def list_work_orders(
    plant_id: str = "helios-50",
    status: Optional[str] = None,
    asset_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    query = db.query(WorkOrder).filter(WorkOrder.plant_id == plant_id)
    if status:
        query = query.filter(WorkOrder.status == status)
    if asset_id:
        query = query.filter(WorkOrder.asset_id == asset_id)
    wos = query.order_by(WorkOrder.created_at.desc()).all()

    return [{
        "id": w.id,
        "work_order_number": w.work_order_number,
        "plant_id": w.plant_id,
        "asset_id": w.asset_id,
        "title": w.title,
        "description": w.description,
        "priority": w.priority,
        "status": w.status,
        "assigned_technician": w.assigned_technician,
        "estimated_hours": w.estimated_hours,
        "actual_hours": w.actual_hours,
        "procedure_code": w.procedure_code,
        "safety_interlock_verified": w.safety_interlock_verified,
        "loto_applied": w.loto_applied,
        "created_at": w.created_at.isoformat()
    } for w in wos]

@router.post("/create", response_model=dict)
def create_work_order(
    data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.OPERATIONS, UserRole.TECHNICIAN, UserRole.ADMIN]))
):
    # Verify asset exists
    asset = db.query(Asset).filter(Asset.id == data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=400, detail=f"Asset {data.asset_id} does not exist.")

    wo_num = f"WO-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    wo = WorkOrder(
        work_order_number=wo_num,
        plant_id=data.plant_id,
        asset_id=data.asset_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        status="assigned",
        assigned_technician=data.assigned_technician,
        estimated_hours=data.estimated_hours,
        procedure_code=data.procedure_code,
        safety_interlock_verified=False,
        loto_applied=False
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)

    return {"message": "Work order created successfully", "work_order_number": wo.work_order_number, "id": wo.id}

@router.patch("/{id}/update", response_model=dict)
def update_work_order(
    id: int,
    data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    if data.status is not None:
        wo.status = data.status
    if data.assigned_technician is not None:
        wo.assigned_technician = data.assigned_technician
    if data.actual_hours is not None:
        wo.actual_hours = data.actual_hours
    if data.safety_interlock_verified is not None:
        wo.safety_interlock_verified = data.safety_interlock_verified
    if data.loto_applied is not None:
        wo.loto_applied = data.loto_applied

    wo.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Work order updated successfully", "id": wo.id}

@router.post("/{id}/verify-safety", response_model=dict)
def verify_safety_and_loto(
    id: int,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.TECHNICIAN, UserRole.ADMIN]))
):
    """
    Certifies that Lockout/Tagout (LOTO) isolation was physically verified
    and safety interlocks are confirmed open before mechanical or electrical work begins.
    """
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    wo.safety_interlock_verified = True
    wo.loto_applied = True
    wo.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": f"Safety interlock & LOTO confirmed for {wo.work_order_number}. Enclosure authorized for physical inspection.",
        "safety_interlock_verified": True,
        "loto_applied": True
    }
