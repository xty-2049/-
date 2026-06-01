"""Geographic clustering for assigning attractions to travel days."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..models.schemas import Attraction
from .geo_utils import haversine_distance_meters


@dataclass
class ClusterResult:
    clusters: List[List[Attraction]]
    cluster_count: int
    reassigned_count: int


class AttractionClusterService:
    """Assign nearby attractions to the same day with lightweight K-Means."""

    def cluster_by_days(self, attractions: List[Attraction], days: int) -> ClusterResult:
        valid = [item for item in attractions if item.location]
        if not valid or days <= 1:
            return ClusterResult([valid], 1 if valid else 0, 0)

        cluster_count = min(days, len(valid))
        centroids = self._initial_centroids(valid, cluster_count)
        assignments: Dict[int, int] = {}

        for _ in range(20):
            changed = False
            new_assignments: Dict[int, int] = {}

            for index, attraction in enumerate(valid):
                nearest = self._nearest_centroid(attraction, centroids)
                new_assignments[index] = nearest
                if assignments.get(index) != nearest:
                    changed = True

            assignments = new_assignments
            centroids = self._recompute_centroids(valid, assignments, centroids)
            if not changed:
                break

        clusters = [[] for _ in range(cluster_count)]
        for index, attraction in enumerate(valid):
            clusters[assignments.get(index, 0)].append(attraction)

        clusters = self._balance_clusters([cluster for cluster in clusters if cluster], days)
        reassigned_count = sum(
            1 for old, new in zip(valid, [item for cluster in clusters for item in cluster]) if old.name != new.name
        )
        return ClusterResult(clusters, len(clusters), reassigned_count)

    def _initial_centroids(self, attractions: List[Attraction], count: int) -> List[Tuple[float, float]]:
        ordered = sorted(attractions, key=lambda item: (item.location.longitude, item.location.latitude))
        if count == 1:
            selected = [ordered[len(ordered) // 2]]
        else:
            selected = [
                ordered[round(i * (len(ordered) - 1) / (count - 1))]
                for i in range(count)
            ]
        return [(item.location.longitude, item.location.latitude) for item in selected]

    def _nearest_centroid(self, attraction: Attraction, centroids: List[Tuple[float, float]]) -> int:
        return min(
            range(len(centroids)),
            key=lambda index: haversine_distance_meters(
                attraction.location.longitude,
                attraction.location.latitude,
                centroids[index][0],
                centroids[index][1],
            ),
        )

    def _recompute_centroids(
        self,
        attractions: List[Attraction],
        assignments: Dict[int, int],
        old_centroids: List[Tuple[float, float]],
    ) -> List[Tuple[float, float]]:
        centroids: List[Tuple[float, float]] = []
        for cluster_index in range(len(old_centroids)):
            cluster = [
                attraction
                for index, attraction in enumerate(attractions)
                if assignments.get(index) == cluster_index
            ]
            if not cluster:
                centroids.append(old_centroids[cluster_index])
                continue
            centroids.append(
                (
                    sum(item.location.longitude for item in cluster) / len(cluster),
                    sum(item.location.latitude for item in cluster) / len(cluster),
                )
            )
        return centroids

    def _balance_clusters(self, clusters: List[List[Attraction]], days: int) -> List[List[Attraction]]:
        if len(clusters) >= days:
            return clusters[:days]

        clusters = [cluster[:] for cluster in clusters]
        while len(clusters) < days:
            largest_index = max(range(len(clusters)), key=lambda index: len(clusters[index]))
            if len(clusters[largest_index]) <= 1:
                break
            moved = clusters[largest_index].pop()
            clusters.append([moved])

        return clusters
