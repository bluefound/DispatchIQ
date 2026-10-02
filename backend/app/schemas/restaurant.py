from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RestaurantBase(BaseModel):
    name: str
    address: str
    phone: str | None = None
    latitude: float
    longitude: float
    avg_prep_time: float = 15.0
    zone: str


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    avg_prep_time: float | None = None
    is_active: bool | None = None
    zone: str | None = None


class RestaurantResponse(RestaurantBase):
    id: UUID
    rating: float
    total_orders: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
