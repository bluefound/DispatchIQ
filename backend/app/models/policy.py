"""
Policy model — operational rules that gate dispatch and AI actions.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Policy rules defined as JSON for flexibility
    # Example: {"max_distance_km": 10, "max_active_orders": 3, "requires_approval": false}
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Policy metadata
    policy_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="e.g., driver_assignment, zone_restriction, capacity, approval"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False,
        comment="Lower number = higher priority"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Policy {self.name} active={self.is_active}>"
