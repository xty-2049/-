"""Geographic helpers for clustering and route optimization."""

from math import asin, cos, radians, sin, sqrt


def haversine_distance_meters(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Return great-circle distance between two coordinates in meters."""
    radius = 6371000
    lon1_r, lat1_r, lon2_r, lat2_r = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))
