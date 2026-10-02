from dataclasses import dataclass
from typing import Any
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from app.utils.geo import estimate_travel_time_minutes, haversine_distance


@dataclass
class CandidateDriver:
    driver_id: str
    latitude: float
    longitude: float
    rating: float
    active_orders: int
    capacity: int
    vehicle_type: str
    current_zone: str | None = None


@dataclass
class OrderTarget:
    order_id: str
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    priority: str = "normal"
    zone: str | None = None


@dataclass
class OptimizationCandidateResult:
    driver_id: str
    score: float
    distance_km: float
    estimated_eta_minutes: float
    rank: int
    scoring_details: dict[str, Any]


class DispatchOptimizer:
    def __init__(
        self,
        weight_proximity: float = 0.4,
        weight_workload: float = 0.2,
        weight_rating: float = 0.2,
        weight_eta: float = 0.2,
    ):
        self.weight_proximity = weight_proximity
        self.weight_workload = weight_workload
        self.weight_rating = weight_rating
        self.weight_eta = weight_eta

    def score_driver(
        self, driver: CandidateDriver, order: OrderTarget
    ) -> OptimizationCandidateResult:
        dist_km = haversine_distance(
            driver.latitude, driver.longitude, order.pickup_latitude, order.pickup_longitude
        )
        eta_min = estimate_travel_time_minutes(dist_km)

        proximity_score = max(0.0, 100.0 - (dist_km * 5.0))
        workload_ratio = driver.active_orders / max(1, driver.capacity)
        workload_score = max(0.0, (1.0 - workload_ratio) * 100.0)
        rating_score = (driver.rating / 5.0) * 100.0
        eta_score = max(0.0, 100.0 - (eta_min * 2.0))

        total_score = (
            (self.weight_proximity * proximity_score)
            + (self.weight_workload * workload_score)
            + (self.weight_rating * rating_score)
            + (self.weight_eta * eta_score)
        )

        details = {
            "proximity_score": round(proximity_score, 2),
            "workload_score": round(workload_score, 2),
            "rating_score": round(rating_score, 2),
            "eta_score": round(eta_score, 2),
            "distance_km": round(dist_km, 2),
            "eta_minutes": round(eta_min, 2),
        }

        return OptimizationCandidateResult(
            driver_id=driver.driver_id,
            score=round(total_score, 2),
            distance_km=round(dist_km, 2),
            estimated_eta_minutes=round(eta_min, 2),
            rank=1,
            scoring_details=details,
        )

    def optimize_single_order(
        self, order: OrderTarget, candidates: list[CandidateDriver]
    ) -> list[OptimizationCandidateResult]:
        if not candidates:
            return []

        results = [self.score_driver(driver, order) for driver in candidates]
        results.sort(key=lambda x: x.score, reverse=True)

        for rank, res in enumerate(results, start=1):
            res.rank = rank

        return results

    def solve_batch_vrp(
        self, orders: list[OrderTarget], drivers: list[CandidateDriver]
    ) -> dict[str, str]:
        if not orders or not drivers:
            return {}

        num_vehicles = len(drivers)
        locations = []
        for d in drivers:
            locations.append((d.latitude, d.longitude))
        for o in orders:
            locations.append((o.pickup_latitude, o.pickup_longitude))

        num_locations = len(locations)
        distance_matrix = []
        for i in range(num_locations):
            row = []
            for j in range(num_locations):
                d = haversine_distance(
                    locations[i][0], locations[i][1], locations[j][0], locations[j][1]
                )
                row.append(int(d * 1000))
            distance_matrix.append(row)

        manager = pywrapcp.RoutingIndexManager(
            num_locations, num_vehicles, list(range(num_vehicles)), list(range(num_vehicles))
        )
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)
        assignments: dict[str, str] = {}

        if solution:
            for vehicle_id in range(num_vehicles):
                index = routing.Start(vehicle_id)
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    if node >= num_vehicles:
                        order_idx = node - num_vehicles
                        if order_idx < len(orders):
                            assignments[orders[order_idx].order_id] = drivers[vehicle_id].driver_id
                    index = solution.Value(routing.NextVar(index))

        return assignments
