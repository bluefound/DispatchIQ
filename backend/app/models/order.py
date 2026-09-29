"""
Order model — orders, items, and delivery event tracking.
"""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    """Order lifecycle status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    ASSIGNED = "assigned"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderPriority(str, enum.Enum):
    """Order priority level."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryEventType(str, enum.Enum):
    """Types of delivery events for tracking."""

    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_EN_ROUTE_PICKUP = "driver_en_route_pickup"
    DRIVER_AT_PICKUP = "driver_at_pickup"
    ORDER_PICKED_UP = "order_picked_up"
    DRIVER_EN_ROUTE_DELIVERY = "driver_en_route_delivery"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FAILED = "order_failed"
    LOCATION_UPDATE = "location_update"
    ETA_UPDATED = "eta_updated"
    ANOMALY_DETECTED = "anomaly_detected"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # Customer info
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Locations (PostGIS)
    pickup_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    pickup_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    dropoff_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    dropoff_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Foreign keys
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True, index=True
    )

    # Order details
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True
    )
    priority: Mapped[OrderPriority] = mapped_column(
        Enum(OrderPriority), nullable=False, default=OrderPriority.NORMAL
    )
    items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Time estimates
    estimated_prep_time: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Minutes"
    )
    estimated_delivery_time: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Minutes"
    )
    actual_delivery_time: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Minutes"
    )
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Notes
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship(back_populates="orders", lazy="selectin")  # noqa: F821
    driver: Mapped["Driver | None"] = relationship(back_populates="orders", lazy="selectin")  # noqa: F821
    events: Mapped[list["DeliveryEvent"]] = relationship(
        back_populates="order", lazy="noload", order_by="DeliveryEvent.created_at"
    )
    dispatch_decisions: Mapped[list["DispatchDecision"]] = relationship(  # noqa: F821
        back_populates="order", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number} status={self.status.value}>"


class OrderItem(Base):
    """Individual items in an order."""

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<OrderItem {self.name} x{self.quantity}>"


class DeliveryEvent(Base):
    """Granular delivery event tracking for audit and analytics."""

    __tablename__ = "delivery_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True
    )
    event_type: Mapped[DeliveryEventType] = mapped_column(
        Enum(DeliveryEventType), nullable=False, index=True
    )
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="events")

    def __repr__(self) -> str:
        return f"<DeliveryEvent {self.event_type.value} order={self.order_id}>"
