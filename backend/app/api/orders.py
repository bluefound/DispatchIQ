import random
import string
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.models.order import DeliveryEvent, DeliveryEventType, Order, OrderStatus
from app.schemas.order import DeliveryEventResponse, OrderCreate, OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_number() -> str:
    digits = "".join(random.choices(string.digits, k=6))
    return f"ORD-{digits}"


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    session: SessionDep,
    status: OrderStatus | None = None,
    driver_id: UUID | None = None,
    restaurant_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = select(Order)
    if status:
        stmt = stmt.where(Order.status == status)
    if driver_id:
        stmt = stmt.where(Order.driver_id == driver_id)
    if restaurant_id:
        stmt = stmt.where(Order.restaurant_id == restaurant_id)
    stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    session: SessionDep,
    _: CurrentUserDep,
):
    pickup_wkt = WKTElement(f"POINT({order_in.pickup_longitude} {order_in.pickup_latitude})", srid=4326)
    dropoff_wkt = WKTElement(f"POINT({order_in.dropoff_longitude} {order_in.dropoff_latitude})", srid=4326)

    items_data = [item.model_dump() for item in order_in.items] if order_in.items else []
    total_amount = sum(item["unit_price"] * item["quantity"] for item in items_data)
    item_count = sum(item["quantity"] for item in items_data)

    order = Order(
        order_number=generate_order_number(),
        customer_name=order_in.customer_name,
        customer_phone=order_in.customer_phone,
        customer_address=order_in.customer_address,
        pickup_location=pickup_wkt,
        pickup_latitude=order_in.pickup_latitude,
        pickup_longitude=order_in.pickup_longitude,
        dropoff_location=dropoff_wkt,
        dropoff_latitude=order_in.dropoff_latitude,
        dropoff_longitude=order_in.dropoff_longitude,
        restaurant_id=order_in.restaurant_id,
        priority=order_in.priority,
        items=items_data,
        total_amount=total_amount,
        item_count=item_count,
        special_instructions=order_in.special_instructions,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    await session.flush()

    event = DeliveryEvent(
        order_id=order.id,
        event_type=DeliveryEventType.ORDER_CREATED,
        description=f"Order {order.order_number} created",
    )
    session.add(event)

    await session.commit()
    await session.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: UUID, session: SessionDep):
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_in: OrderUpdate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    old_status = order.status
    update_data = order_in.model_dump(exclude_unset=True)

    now = datetime.now(timezone.utc)
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == OrderStatus.CONFIRMED and not order.confirmed_at:
            order.confirmed_at = now
        elif new_status == OrderStatus.ASSIGNED and not order.assigned_at:
            order.assigned_at = now
        elif new_status == OrderStatus.PICKED_UP and not order.picked_up_at:
            order.picked_up_at = now
        elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = now
        elif new_status == OrderStatus.CANCELLED and not order.cancelled_at:
            order.cancelled_at = now

    for field, value in update_data.items():
        setattr(order, field, value)

    if old_status != order.status:
        event = DeliveryEvent(
            order_id=order.id,
            driver_id=order.driver_id,
            event_type=DeliveryEventType[f"ORDER_{order.status.value.upper()}"]
            if order.status.value.upper() in DeliveryEventType.__members__
            else DeliveryEventType.LOCATION_UPDATE,
            description=f"Order status changed from {old_status.value} to {order.status.value}",
        )
        session.add(event)

    await session.commit()
    await session.refresh(order)
    return order


@router.get("/{order_id}/events", response_model=list[DeliveryEventResponse])
async def get_order_events(order_id: UUID, session: SessionDep):
    stmt = (
        select(DeliveryEvent)
        .where(DeliveryEvent.order_id == order_id)
        .order_by(DeliveryEvent.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
