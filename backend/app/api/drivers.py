from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.models.driver import Driver, DriverLocation, DriverStatus
from app.schemas.driver import DriverCreate, DriverLocationUpdate, DriverResponse, DriverUpdate

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
async def list_drivers(
    session: SessionDep,
    status: DriverStatus | None = None,
    is_available: bool | None = None,
    zone: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = select(Driver)
    if status:
        stmt = stmt.where(Driver.status == status)
    if is_available is not None:
        stmt = stmt.where(Driver.is_available == is_available)
    if zone:
        stmt = stmt.where(Driver.current_zone == zone)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_in: DriverCreate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Driver).where(Driver.user_id == driver_in.user_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver profile already exists for this user",
        )

    driver = Driver(
        user_id=driver_in.user_id,
        vehicle_type=driver_in.vehicle_type,
        license_plate=driver_in.license_plate,
        phone=driver_in.phone,
        capacity=driver_in.capacity,
        current_zone=driver_in.current_zone,
    )
    session.add(driver)
    await session.commit()
    await session.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: UUID, session: SessionDep):
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: UUID,
    driver_in: DriverUpdate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    update_data = driver_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    await session.commit()
    await session.refresh(driver)
    return driver


@router.post("/{driver_id}/location", response_model=DriverResponse)
async def update_driver_location(
    driver_id: UUID,
    loc_in: DriverLocationUpdate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await session.execute(stmt)
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    wkt_location = WKTElement(f"POINT({loc_in.longitude} {loc_in.latitude})", srid=4326)
    driver.current_latitude = loc_in.latitude
    driver.current_longitude = loc_in.longitude
    driver.current_location = wkt_location
    driver.last_location_update = datetime.now(timezone.utc)

    loc_history = DriverLocation(
        driver_id=driver.id,
        location=wkt_location,
        latitude=loc_in.latitude,
        longitude=loc_in.longitude,
        speed=loc_in.speed,
        heading=loc_in.heading,
    )
    session.add(loc_history)

    await session.commit()
    await session.refresh(driver)
    return driver
