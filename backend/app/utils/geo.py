import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def estimate_travel_time_minutes(
    distance_km: float, vehicle_speed_kmh: float = 30.0, traffic_factor: float = 1.2
) -> float:
    base_hours = distance_km / vehicle_speed_kmh
    return base_hours * 60.0 * traffic_factor
