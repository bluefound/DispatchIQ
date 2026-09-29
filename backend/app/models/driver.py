"""
Driver model — driver profiles, location tracking, and status management.
"""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DriverStatus(str, enum.Enum):
    """Driver operational status."""

    OFFLINE = "offline"
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    EN_ROUTE_PICKUP = "en_route_pickup"
    AT_PICKUP = "at_pickup"
    DELIVERING = "delivering"
    RETURNING = "returning"


class VehicleType(str, enum.Enum):
    """Vehicle types supported by the platform."""

    MOTORCYCLE = "motorcycle"
    CAR = "car"
    BICYCLE = "bicycle"
    VAN = "van"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType), nullable=False, default=VehicleType.MOTORCYCLE
    )
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus), nullable=False, default=DriverStatus.OFFLINE, index=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Current position (PostGIS)
    current_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Performance metrics
    current_zone: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    capacity: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False, comment="Max concurrent orders"
    )
    active_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="driver_profile", lazy="selectin")  # noqa: F821
    orders: Mapped[list["Order"]] = relationship(back_populates="driver", lazy="selectin")  # noqa: F821
    location_history: Mapped[list["DriverLocation"]] = relationship(
        back_populates="driver", lazy="noload"
    )
    dispatch_decisions: Mapped[list["DispatchDecision"]] = relationship(  # noqa: F821
        back_populates="driver", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Driver {self.id} status={self.status.value}>"


class DriverLocation(Base):
    """Historical driver location records for tracking and analytics."""

    __tablename__ = "driver_locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Speed in km/h")
    heading: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Heading in degrees (0-360)"
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    driver: Mapped["Driver"] = relationship(back_populates="location_history")

    def __repr__(self) -> str:
        return f"<DriverLocation driver={self.driver_id} at={self.recorded_at}>"
