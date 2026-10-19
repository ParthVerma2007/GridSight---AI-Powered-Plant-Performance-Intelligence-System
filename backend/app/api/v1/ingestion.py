from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.ingestion.pipeline import IngestionPipeline
from app.models.quarantine import IngestionBatch, QuarantineRecord
from app.schemas.ingestion import CSVUploadResponse, IngestionReport, QuarantineItem
from app.auth.rbac import get_current_role, require_role, UserRole

router = APIRouter(prefix="/ingestion", tags=["Ingestion & Validation"])

@router.post("/upload", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    file_type: str = Form(..., description="generation | forecast | equipment | weather | maintenance | workforce | financial | external_events"),
    plant_id: str = Form("helios-50"),
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(require_role([UserRole.OPERATIONS, UserRole.ADMIN]))
):
    """
    Upload and parse CSV dataset into canonical plant model with validation and quarantine.
    Preserves original files, records row references, detects duplicates, normalizes timestamps and units.
    """
    if not file.filename.endswith(".csv") and not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid CSV file (.csv)"
        )

    content_bytes = await file.read()
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("latin-1")

    pipeline = IngestionPipeline(db)
    report = pipeline.ingest_csv(
        file_content=content_str,
        filename=file.filename,
        file_type=file_type,
        plant_id=plant_id
    )

    return CSVUploadResponse(
        message=f"Dataset processed successfully. Status: {report.status}",
        batch_id=report.batch_id,
        report=report
    )

@router.get("/batches", response_model=List[dict])
def list_ingestion_batches(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Lists recent ingestion batches and summaries.
    """
    batches = db.query(IngestionBatch).order_by(IngestionBatch.created_at.desc()).limit(limit).all()
    return [{
        "batch_id": b.batch_id,
        "source_file": b.source_file,
        "file_type": b.file_type,
        "total_records": b.total_records,
        "valid_records": b.valid_records,
        "quarantined_records": b.quarantined_records,
        "success_rate_pct": round((b.valid_records / b.total_records * 100.0), 1) if b.total_records > 0 else 0.0,
        "status": b.status,
        "summary": b.summary,
        "created_at": b.created_at.isoformat()
    } for b in batches]

@router.get("/quarantine", response_model=List[QuarantineItem])
def get_quarantined_records(
    batch_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_role: UserRole = Depends(get_current_role)
):
    """
    Inspects quarantined records with failure reasons and source-row provenance.
    """
    query = db.query(QuarantineRecord)
    if batch_id:
        query = query.filter(QuarantineRecord.batch_id == batch_id)
    records = query.order_by(QuarantineRecord.quarantined_at.desc()).limit(limit).all()

    return [QuarantineItem(
        id=r.id,
        source_file=r.source_file,
        row_index=r.row_index,
        raw_content=r.raw_content,
        error_type=r.error_type,
        error_detail=r.error_detail,
        quarantined_at=r.quarantined_at
    ) for r in records]
