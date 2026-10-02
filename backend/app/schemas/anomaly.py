from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.anomaly import AnomalyType, AnomalySeverity, AnomalyStatus


class AnomalyCreate(BaseModel):
    type: AnomalyType
    severity: AnomalySeverity
    entity_type: str
    entity_id: str
    description: str
    details: dict | None = None
    detection_method: str = "rule_based"
    confidence: float | None = None


class AnomalyUpdate(BaseModel):
    status: AnomalyStatus | None = None
    resolution_notes: str | None = None
    resolved_by: str | None = None


class AnomalyResponse(AnomalyCreate):
    id: UUID
    status: AnomalyStatus
    detected_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)
