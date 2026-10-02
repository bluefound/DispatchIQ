from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.order import OrderStatus, OrderPriority, DeliveryEventType


class OrderItemSchema(BaseModel):
    name: str
    quantity: int = 1
    unit_price: float
    notes: str | None = None


class OrderBase(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    restaurant_id: UUID
    priority: OrderPriority = OrderPriority.NORMAL
    items: list[OrderItemSchema] | None = None
    special_instructions: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    priority: OrderPriority | None = None
    driver_id: UUID | None = None
    estimated_prep_time: float | None = None
    estimated_delivery_time: float | None = None
    actual_delivery_time: float | None = None


class DeliveryEventResponse(BaseModel):
    id: UUID
    order_id: UUID
    driver_id: UUID | None = None
    event_type: DeliveryEventType
    latitude: float | None = None
    longitude: float | None = None
    metadata_: dict | None = None
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(OrderBase):
    id: UUID
    order_number: str
    driver_id: UUID | None = None
    status: OrderStatus
    total_amount: float
    item_count: int
    estimated_prep_time: float | None = None
    estimated_delivery_time: float | None = None
    actual_delivery_time: float | None = None
    distance_km: float | None = None
    created_at: datetime
    confirmed_at: datetime | None = None
    assigned_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
