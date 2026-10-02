from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.dispatch import DispatchMethod, DispatchStatus


class DispatchRequest(BaseModel):
    order_id: UUID
    preferred_driver_id: UUID | None = None
    force: bool = False


class BatchDispatchRequest(BaseModel):
    order_ids: list[UUID]
    max_drivers_per_order: int = 5


class DispatchDecisionResponse(BaseModel):
    id: UUID
    order_id: UUID
    driver_id: UUID
    score: float
    distance_km: float
    estimated_eta_minutes: float
    optimization_method: DispatchMethod
    rank: int
    scoring_details: dict | None = None
    status: DispatchStatus
    policy_approved: bool
    policy_reason: str | None = None
    policy_violations: dict | None = None
    decided_at: datetime
    accepted_at: datetime | None = None
    rejected_at: datetime | None = None
    reviewed_by: str | None = None

    model_config = ConfigDict(from_attributes=True)
