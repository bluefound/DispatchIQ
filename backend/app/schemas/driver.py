from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.driver import DriverStatus, VehicleType


class DriverBase(BaseModel):
    vehicle_type: VehicleType = VehicleType.MOTORCYCLE
    license_plate: str
    phone: str
    capacity: int = 3
    current_zone: str | None = None


class DriverCreate(DriverBase):
    user_id: UUID


class DriverUpdate(BaseModel):
    vehicle_type: VehicleType | None = None
    license_plate: str | None = None
    phone: str | None = None
    status: DriverStatus | None = None
    is_available: bool | None = None
    current_zone: str | None = None
    capacity: int | None = None


class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    speed: float | None = None
    heading: float | None = None


class DriverResponse(DriverBase):
    id: UUID
    user_id: UUID
    status: DriverStatus
    is_available: bool
    current_latitude: float | None = None
    current_longitude: float | None = None
    last_location_update: datetime | None = None
    active_orders: int
    rating: float
    total_deliveries: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
