"""
AI Recommendation & Model Prediction models — audit trails for AI and ML outputs.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RecommendationStatus(str, enum.Enum):
    """Status of an AI recommendation."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    EXPIRED = "expired"


class AIRecommendation(Base):
    """Stores AI-generated operational recommendations."""

    __tablename__ = "ai_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trigger_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="e.g., anomaly, user_query, scheduled_analysis"
    )
    trigger_entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Action details
    proposed_actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.PENDING, index=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AIRecommendation {self.id} status={self.status.value}>"


class ModelPrediction(Base):
    """Audit trail for ML model predictions — enables performance tracking."""

    __tablename__ = "model_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Prediction details
    input_features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    prediction: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Actuals (filled in later when ground truth is known)
    actual_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Prediction error (actual - predicted)"
    )

    # Context
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<ModelPrediction {self.model_name}@{self.model_version}>"
