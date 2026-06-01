"""Daily route ordering with nearest-neighbor and 2-opt optimization."""

from dataclasses import dataclass
from typing import List

from ..models.schemas import Attraction
from .geo_utils import haversine_distance_meters


@dataclass
class RouteOptimizationResult:
    attractions: List[Attraction]
    original_distance_meters: float
    optimized_distance_meters: float

    @property
    def saved_distance_meters(self) -> float:
        return max(0.0, self.original_distance_meters - self.optimized_distance_meters)


class RouteOptimizer:
    """Optimize the visit order of attractions inside one day."""

    def optimize(self, attractions: List[Attraction]) -> RouteOptimizationResult:
        if len(attractions) < 3:
            distance = self.total_distance(attractions)
            return RouteOptimizationResult(attractions, distance, distance)

        original_distance = self.total_distance(attractions)
        nearest_order = self._nearest_neighbor(attractions)
        optimized_order = self._two_opt(nearest_order)
        optimized_distance = self.total_distance(optimized_order)

        if optimized_distance > original_distance:
            return RouteOptimizationResult(attractions, original_distance, original_distance)

        return RouteOptimizationResult(optimized_order, original_distance, optimized_distance)

    def total_distance(self, attractions: List[Attraction]) -> float:
        distance = 0.0
        for current, nxt in zip(attractions, attractions[1:]):
            distance += haversine_distance_meters(
                current.location.longitude,
                current.location.latitude,
                nxt.location.longitude,
                nxt.location.latitude,
            )
        return distance

    def _nearest_neighbor(self, attractions: List[Attraction]) -> List[Attraction]:
        remaining = attractions[:]
        route = [remaining.pop(0)]

        while remaining:
            current = route[-1]
            next_index = min(
                range(len(remaining)),
                key=lambda i: haversine_distance_meters(
                    current.location.longitude,
                    current.location.latitude,
                    remaining[i].location.longitude,
                    remaining[i].location.latitude,
                ),
            )
            route.append(remaining.pop(next_index))

        return route

    def _two_opt(self, route: List[Attraction]) -> List[Attraction]:
        best = route[:]
        improved = True

        while improved:
            improved = False
            best_distance = self.total_distance(best)
            for i in range(1, len(best) - 2):
                for j in range(i + 1, len(best)):
                    if j - i == 1:
                        continue
                    candidate = best[:i] + best[i:j][::-1] + best[j:]
                    candidate_distance = self.total_distance(candidate)
                    if candidate_distance + 1e-6 < best_distance:
                        best = candidate
                        improved = True
                        break
                if improved:
                    break

        return best
