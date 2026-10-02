import asyncio
import random
from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory
from app.models.driver import Driver, DriverStatus, VehicleType
from app.models.order import Order, OrderPriority, OrderStatus
from app.models.policy import Policy
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.utils.security import hash_password

LAGOS_ZONES = {
    "Lekki": {"lat": 6.4584, "lng": 3.4816},
    "Victoria Island": {"lat": 6.4281, "lng": 3.4219},
    "Ikeja": {"lat": 6.6018, "lng": 3.3515},
    "Yaba": {"lat": 6.5095, "lng": 3.3711},
}


async def seed():
    async with async_session_factory() as session:
        admin_user = User(
            email="admin@dispatchiq.com",
            password_hash=hash_password("AdminPass123!"),
            full_name="System Admin",
            role=UserRole.ADMIN,
        )
        dispatcher_user = User(
            email="dispatcher@dispatchiq.com",
            password_hash=hash_password("DispatchPass123!"),
            full_name="Lead Dispatcher",
            role=UserRole.DISPATCHER,
        )
        session.add_all([admin_user, dispatcher_user])
        await session.flush()

        restaurants = []
        rest_names = [
            ("Kilimanjaro Lekki", "Lekki", 6.4580, 3.4810),
            ("Chicken Republic VI", "Victoria Island", 6.4290, 3.4225),
            ("Mega Plaza Food Court", "Victoria Island", 6.4270, 3.4210),
            ("The Place Ikeja", "Ikeja", 6.6025, 3.3520),
            ("Suya Spot Yaba", "Yaba", 6.5100, 3.3720),
        ]
        for name, zone, lat, lng in rest_names:
            r = Restaurant(
                name=name,
                address=f"Plot 12, {zone} Expressway, Lagos",
                phone="+2348012345678",
                latitude=lat,
                longitude=lng,
                location=WKTElement(f"POINT({lng} {lat})", srid=4326),
                avg_prep_time=random.uniform(12.0, 25.0),
                rating=random.uniform(4.0, 4.9),
                zone=zone,
            )
            session.add(r)
            restaurants.append(r)
        await session.flush()

        drivers = []
        for i in range(1, 11):
            zone_name = list(LAGOS_ZONES.keys())[i % len(LAGOS_ZONES)]
            base_coords = LAGOS_ZONES[zone_name]
            d_lat = base_coords["lat"] + random.uniform(-0.01, 0.01)
            d_lng = base_coords["lng"] + random.uniform(-0.01, 0.01)

            u = User(
                email=f"driver{i}@dispatchiq.com",
                password_hash=hash_password("DriverPass123!"),
                full_name=f"Driver {i}",
                role=UserRole.DRIVER,
            )
            session.add(u)
            await session.flush()

            d = Driver(
                user_id=u.id,
                vehicle_type=VehicleType.MOTORCYCLE if i % 2 == 0 else VehicleType.CAR,
                license_plate=f"LND-{100+i}AA",
                phone=f"+234809000000{i}",
                status=DriverStatus.AVAILABLE,
                is_available=True,
                current_latitude=d_lat,
                current_longitude=d_lng,
                current_location=WKTElement(f"POINT({d_lng} {d_lat})", srid=4326),
                current_zone=zone_name,
                rating=round(random.uniform(4.2, 5.0), 1),
                total_deliveries=random.randint(20, 200),
            )
            session.add(d)
            drivers.append(d)
        await session.flush()

        policies = [
            Policy(
                name="Maximum Distance Limit",
                description="Prevents driver assignment if pickup is > 15km away",
                rules={"max_distance_km": 15.0},
                policy_type="driver_assignment",
                priority=10,
            ),
            Policy(
                name="Driver Workload Limit",
                description="Caps driver concurrent active orders at capacity",
                rules={"max_active_orders": 3},
                policy_type="capacity",
                priority=20,
            ),
            Policy(
                name="High Value Approval Gating",
                description="Requires manual sign-off for urgent or high-value orders",
                rules={"requires_human_approval": False},
                policy_type="approval",
                priority=30,
            ),
        ]
        session.add_all(policies)

        for i in range(1, 6):
            rest = random.choice(restaurants)
            o_lat = rest.latitude + random.uniform(-0.02, 0.02)
            o_lng = rest.longitude + random.uniform(-0.02, 0.02)

            o = Order(
                order_number=f"ORD-1000{i}",
                customer_name=f"Customer {i}",
                customer_phone=f"+234700000000{i}",
                customer_address=f"Block {i}, Admiralty Way, Lekki",
                pickup_latitude=rest.latitude,
                pickup_longitude=rest.longitude,
                pickup_location=rest.location,
                dropoff_latitude=o_lat,
                dropoff_longitude=o_lng,
                dropoff_location=WKTElement(f"POINT({o_lng} {o_lat})", srid=4326),
                restaurant_id=rest.id,
                priority=OrderPriority.NORMAL if i % 2 == 0 else OrderPriority.HIGH,
                items=[{"name": "Jollof Rice Special", "quantity": 2, "unit_price": 2500.0}],
                total_amount=5000.0,
                item_count=2,
                status=OrderStatus.PENDING,
            )
            session.add(o)

        await session.commit()
        print("Successfully seeded DispatchIQ database!")


if __name__ == "__main__":
    asyncio.run(seed())
