"""
Anomaly model — operational anomaly detection and tracking.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnomalyType(str, enum.Enum):
    """Types of operational anomalies."""

    STALLED_DELIVERY = "stalled_delivery"
    ROUTE_DEVIATION = "route_deviation"
    LONG_DELIVERY = "long_delivery"
    CANCELLATION_SPIKE = "cancellation_spike"
    PREP_TIME_SPIKE = "prep_time_spike"
    ETA_MISS = "eta_miss"
    DRIVER_STATIONARY = "driver_stationary"
    UNUSUAL_PATTERN = "unusual_pattern"


class AnomalySeverity(str, enum.Enum):
    """Severity levels for anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(str, enum.Enum):
    """Anomaly resolution status."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[AnomalyType] = mapped_column(Enum(AnomalyType), nullable=False, index=True)
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity), nullable=False, index=True
    )
    status: Mapped[AnomalyStatus] = mapped_column(
        Enum(AnomalyStatus), nullable=False, default=AnomalyStatus.OPEN, index=True
    )

    # Entity reference (polymorphic — can reference order, driver, restaurant, zone)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Detection metadata
    detection_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="rule_based"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Anomaly {self.type.value} severity={self.severity.value}>"
