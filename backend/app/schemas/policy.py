from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PolicyBase(BaseModel):
    name: str
    description: str
    rules: dict
    policy_type: str = "driver_assignment"
    is_active: bool = True
    priority: int = 100


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rules: dict | None = None
    policy_type: str | None = None
    is_active: bool | None = None
    priority: int | None = None


class PolicyResponse(PolicyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    model_config = ConfigDict(from_attributes=True)
