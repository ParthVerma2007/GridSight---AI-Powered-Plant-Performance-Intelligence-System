from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuarantineItem(BaseModel):
    id: int
    source_file: str
    row_index: int
    raw_content: str
    error_type: str
    error_detail: str
    quarantined_at: datetime

class IngestionReport(BaseModel):
    batch_id: str
    source_file: str
    file_type: str
    total_records: int
    valid_records: int
    quarantined_records: int
    success_rate_pct: float
    status: str
    quarantined_items: List[QuarantineItem] = []
    created_at: datetime
    summary: str

class CSVUploadResponse(BaseModel):
    message: str
    batch_id: str
    report: IngestionReport
