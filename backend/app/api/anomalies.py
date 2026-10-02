from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.models.anomaly import Anomaly, AnomalySeverity, AnomalyStatus, AnomalyType
from app.schemas.anomaly import AnomalyCreate, AnomalyResponse, AnomalyUpdate

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("", response_model=list[AnomalyResponse])
async def list_anomalies(
    session: SessionDep,
    status: AnomalyStatus | None = None,
    severity: AnomalySeverity | None = None,
    anomaly_type: AnomalyType | None = None,
    limit: int = 100,
):
    stmt = select(Anomaly)
    if status:
        stmt = stmt.where(Anomaly.status == status)
    if severity:
        stmt = stmt.where(Anomaly.severity == severity)
    if anomaly_type:
        stmt = stmt.where(Anomaly.type == anomaly_type)
    stmt = stmt.order_by(Anomaly.detected_at.desc()).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=AnomalyResponse, status_code=status.HTTP_201_CREATED)
async def create_anomaly(
    anomaly_in: AnomalyCreate,
    session: SessionDep,
    _: CurrentUserDep,
):
    anomaly = Anomaly(
        type=anomaly_in.type,
        severity=anomaly_in.severity,
        entity_type=anomaly_in.entity_type,
        entity_id=anomaly_in.entity_id,
        description=anomaly_in.description,
        details=anomaly_in.details,
        detection_method=anomaly_in.detection_method,
        confidence=anomaly_in.confidence,
        status=AnomalyStatus.OPEN,
    )
    session.add(anomaly)
    await session.commit()
    await session.refresh(anomaly)
    return anomaly


@router.patch("/{anomaly_id}", response_model=AnomalyResponse)
async def update_anomaly(
    anomaly_id: UUID,
    anomaly_in: AnomalyUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    stmt = select(Anomaly).where(Anomaly.id == anomaly_id)
    res = await session.execute(stmt)
    anomaly = res.scalar_one_or_none()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")

    if anomaly_in.status:
        anomaly.status = anomaly_in.status
        now = datetime.now(timezone.utc)
        if anomaly_in.status == AnomalyStatus.ACKNOWLEDGED:
            anomaly.acknowledged_at = now
        elif anomaly_in.status in [AnomalyStatus.RESOLVED, AnomalyStatus.FALSE_POSITIVE]:
            anomaly.resolved_at = now
            anomaly.resolved_by = current_user.email

    if anomaly_in.resolution_notes:
        anomaly.resolution_notes = anomaly_in.resolution_notes

    await session.commit()
    await session.refresh(anomaly)
    return anomaly
