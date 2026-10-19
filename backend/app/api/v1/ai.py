from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.context.builder import ContextPackageBuilder
from app.ai.service import ai_service
from app.schemas.ai import AIExplanationResponse, AIQueryRequest
from app.api.v1.analytics import get_default_time_range
from app.auth.rbac import get_current_role, UserRole

router = APIRouter(prefix="/ai", tags=["AI Intelligence Engine"])

@router.post("/query", response_model=AIExplanationResponse)
async def query_ai_intelligence(
    request: AIQueryRequest,
    plant_id: str = Query("helios-50"),
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Submits role-specific user questions to the AI Intelligence Engine.
    Builds a compact context package containing only verified metrics, events, and evidence,
    and returns a structured response distinguishing verified facts, explanations, hypotheses, and unknowns.
    """
    role = request.role or current_role.value

    # Parse period
    if request.period_start and request.period_end:
        try:
            start_time = datetime.fromisoformat(request.period_start)
            end_time = datetime.fromisoformat(request.period_end)
        except Exception:
            start_time, end_time = get_default_time_range(db, plant_id)
    else:
        start_time, end_time = get_default_time_range(db, plant_id)

    builder = ContextPackageBuilder(db, plant_id)
    context = builder.build_compact_context(
        role=role,
        start_time=start_time,
        end_time=end_time,
        user_question=request.question
    )

    response = await ai_service.generate_explanation(context)
    return response

@router.get("/context-preview", response_model=dict)
def preview_compact_context(
    role: str = Query("OPERATIONS"),
    plant_id: str = Query("helios-50"),
    db: Session = Depends(get_db)
):
    """
    Inspects the compact context package payload sent to the AI (demonstrating dynamic retrieval vs raw CSV dumping).
    """
    start_time, end_time = get_default_time_range(db, plant_id)
    builder = ContextPackageBuilder(db, plant_id)
    context = builder.build_compact_context(role=role, start_time=start_time, end_time=end_time)
    return context.model_dump()
