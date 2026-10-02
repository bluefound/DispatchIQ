from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from geoalchemy2.elements import WKTElement
from sqlalchemy import select, func
from app.api.deps import CurrentUserDep, SessionDep
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("", response_model=list[RestaurantResponse])
async def list_restaurants(
    session: SessionDep,
    zone: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = select(Restaurant)
    if zone:
        stmt = stmt.where(Restaurant.zone == zone)
    if is_active is not None:
        stmt = stmt.where(Restaurant.is_active == is_active)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_in: RestaurantCreate,
    session: SessionDep,
    _: CurrentUserDep,
):
    wkt_location = WKTElement(f"POINT({restaurant_in.longitude} {restaurant_in.latitude})", srid=4326)
    restaurant = Restaurant(
        name=restaurant_in.name,
        address=restaurant_in.address,
        phone=restaurant_in.phone,
        latitude=restaurant_in.latitude,
        longitude=restaurant_in.longitude,
        location=wkt_location,
        avg_prep_time=restaurant_in.avg_prep_time,
        zone=restaurant_in.zone,
    )
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: UUID, session: SessionDep):
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: UUID,
    restaurant_in: RestaurantUpdate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    update_data = restaurant_in.model_dump(exclude_unset=True)
    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.get("latitude", restaurant.latitude)
        lng = update_data.get("longitude", restaurant.longitude)
        update_data["location"] = WKTElement(f"POINT({lng} {lat})", srid=4326)

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    await session.commit()
    await session.refresh(restaurant)
    return restaurant
