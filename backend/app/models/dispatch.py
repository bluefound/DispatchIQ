"""
Dispatch Decision model — records the optimization output for each dispatch.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DispatchMethod(str, enum.Enum):
    """Method used to determine dispatch assignment."""

    OR_TOOLS = "or_tools"
    SCORING = "scoring"
    MANUAL = "manual"
    ROUND_ROBIN = "round_robin"


class DispatchStatus(str, enum.Enum):
    """Status of the dispatch decision."""

    PROPOSED = "proposed"
    POLICY_APPROVED = "policy_approved"
    POLICY_REJECTED = "policy_rejected"
    AWAITING_APPROVAL = "awaiting_approval"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DispatchDecision(Base):
    """Records each dispatch decision for audit and analytics."""

    __tablename__ = "dispatch_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False, index=True
    )

    # Scoring
    score: Mapped[float] = mapped_column(Float, nullable=False, comment="Composite assignment score")
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_eta_minutes: Mapped[float] = mapped_column(Float, nullable=False)

    # Method and ranking
    optimization_method: Mapped[DispatchMethod] = mapped_column(
        Enum(DispatchMethod), nullable=False, default=DispatchMethod.SCORING
    )
    rank: Mapped[int] = mapped_column(default=1, comment="Rank among candidates (1 = best)")

    # Scoring breakdown
    scoring_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Policy evaluation
    status: Mapped[DispatchStatus] = mapped_column(
        Enum(DispatchStatus), nullable=False, default=DispatchStatus.PROPOSED, index=True
    )
    policy_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    policy_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_violations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="dispatch_decisions")  # noqa: F821
    driver: Mapped["Driver"] = relationship(back_populates="dispatch_decisions")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DispatchDecision order={self.order_id} driver={self.driver_id} score={self.score:.2f}>"
