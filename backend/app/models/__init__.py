"""
DispatchIQ — SQLAlchemy ORM Models

All models are imported here for Alembic auto-detection.
"""

from app.models.user import User  # noqa: F401
from app.models.restaurant import Restaurant  # noqa: F401
from app.models.driver import Driver, DriverLocation  # noqa: F401
from app.models.order import Order, OrderItem, DeliveryEvent  # noqa: F401
from app.models.dispatch import DispatchDecision  # noqa: F401
from app.models.anomaly import Anomaly  # noqa: F401
from app.models.policy import Policy  # noqa: F401
from app.models.ai_recommendation import AIRecommendation, ModelPrediction  # noqa: F401

__all__ = [
    "User",
    "Restaurant",
    "Driver",
    "DriverLocation",
    "Order",
    "OrderItem",
    "DeliveryEvent",
    "DispatchDecision",
    "Anomaly",
    "Policy",
    "AIRecommendation",
    "ModelPrediction",
]
