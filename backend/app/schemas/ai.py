from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CompactContextPackage(BaseModel):
    user_role: str  # CEO, OPERATIONS, TECHNICIAN
    plant_id: str
    plant_name: str
    period_start: str
    period_end: str
    verified_metrics: Dict[str, Any]
    attributed_causes: List[Dict[str, Any]]
    related_events: List[Dict[str, Any]]
    equipment_alarms: List[Dict[str, Any]]
    financial_parameters: Dict[str, Any]
    user_question: Optional[str] = None

class AIActionItem(BaseModel):
    priority: str  # P1, P2, P3
    action: str
    owner_role: str
    rationale: str
    safety_precaution: Optional[str] = None

class AIExplanationResponse(BaseModel):
    role: str
    summary: str
    verified_facts: List[str]
    supported_explanations: List[str]
    hypotheses: List[str]
    unknowns: List[str]
    strategic_or_operational_risks: List[str]
    recommended_actions: List[AIActionItem]
    citations_and_evidence: List[str]
    provider_used: str  # 'gemini', 'huggingface', 'fallback'
    validation_status: str  # 'passed_numerical_verification', 'fallback_template'

class AIQueryRequest(BaseModel):
    role: str = "OPERATIONS"  # CEO, OPERATIONS, TECHNICIAN
    question: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
