"""Post-process generated trips with clustering, route and hotel optimization."""

from __future__ import annotations

import copy
from typing import List, Optional, Tuple

from ..models.schemas import Attraction, DayPlan, Hotel, Meal, TripPlan, TripRequest
from .cache_service import get_cache_service
from .cluster_service import AttractionClusterService
from .geo_utils import haversine_distance_meters
from .route_optimizer import RouteOptimizer


class ItineraryOptimizer:
    """Optimize attractions first, then keep hotels spatially consistent."""

    def __init__(self):
        self.cache = get_cache_service()
        self.clusterer = AttractionClusterService()
        self.route_optimizer = RouteOptimizer()

    def optimize_trip(self, trip_plan: TripPlan, request: TripRequest) -> TripPlan:
        all_attractions = self._collect_attractions(trip_plan.days)
        hotel_candidates = self._collect_hotels(trip_plan.days)
        meal_candidates = self._collect_meals(trip_plan.days)

        if len(all_attractions) < 2:
            hotel_summary = self._optimize_hotels_by_day_center(trip_plan, hotel_candidates)
            meal_summary = self._optimize_meals_by_day_anchors(trip_plan, meal_candidates)
            trip_plan.optimization_summary = self._join_summary(
                "景点数量较少，无需路线优化。",
                hotel_summary,
                meal_summary,
            )
            return trip_plan

        cache_key = self.cache.build_key(
            "itinerary-v2-hotel",
            request.city,
            request.travel_days,
            [
                (
                    item.name,
                    round(item.location.longitude, 6),
                    round(item.location.latitude, 6),
                )
                for item in all_attractions
            ],
            [
                (
                    hotel.name,
                    round(hotel.location.longitude, 6),
                    round(hotel.location.latitude, 6),
                )
                for hotel in hotel_candidates
                if hotel.location
            ],
            [
                (
                    meal.name,
                    meal.type,
                    round(meal.location.longitude, 6),
                    round(meal.location.latitude, 6),
                )
                for meal in meal_candidates
                if meal.location
            ],
        )
        cached = self.cache.get("itinerary_optimization", cache_key)
        if cached:
            self._apply_cached_order(trip_plan, cached)
            hotel_summary = self._apply_cached_hotels(trip_plan, cached, hotel_candidates)
            meal_summary = self._apply_cached_meals(trip_plan, cached, meal_candidates)
            trip_plan.optimization_summary = self._join_summary(
                cached["summary"] + "（命中缓存）",
                hotel_summary,
                meal_summary,
            )
            return trip_plan

        original_total = sum(self.route_optimizer.total_distance(day.attractions) for day in trip_plan.days)
        cluster_result = self.clusterer.cluster_by_days(all_attractions, request.travel_days)

        optimized_total = 0.0
        optimized_days: List[DayPlan] = []
        for index, day in enumerate(trip_plan.days):
            attractions = cluster_result.clusters[index] if index < len(cluster_result.clusters) else []
            result = self.route_optimizer.optimize(attractions)
            optimized_total += result.optimized_distance_meters
            day.attractions = result.attractions
            day.day_index = index
            if day.attractions:
                day.description = self._build_day_description(day, index)
            optimized_days.append(day)

        trip_plan.days = optimized_days
        hotel_summary = self._optimize_hotels_by_day_center(trip_plan, hotel_candidates)
        meal_summary = self._optimize_meals_by_day_anchors(trip_plan, meal_candidates)

        saved_km = max(0.0, (original_total - optimized_total) / 1000)
        optimized_km = optimized_total / 1000
        route_summary = (
            f"已按地理位置完成景点区域聚类，并优化每日景点访问顺序；"
            f"优化后预计景点间直线通勤约 {optimized_km:.1f} 公里，"
            f"较原顺序节省约 {saved_km:.1f} 公里。"
        )
        trip_plan.optimization_summary = self._join_summary(route_summary, hotel_summary, meal_summary)

        self.cache.set(
            "itinerary_optimization",
            cache_key,
            {
                "summary": route_summary,
                "days": [[item.name for item in day.attractions] for day in trip_plan.days],
                "hotels": [day.hotel.name if day.hotel else "" for day in trip_plan.days],
                "meals": [
                    [(meal.type, meal.name) for meal in day.meals]
                    for day in trip_plan.days
                ],
            },
            ttl_seconds=7 * 24 * 3600,
        )
        return trip_plan

    def _collect_attractions(self, days: List[DayPlan]) -> List[Attraction]:
        seen = set()
        attractions: List[Attraction] = []
        for day in days:
            for attraction in day.attractions:
                if not attraction.location:
                    continue
                key = (
                    attraction.name,
                    round(attraction.location.longitude, 6),
                    round(attraction.location.latitude, 6),
                )
                if key in seen:
                    continue
                seen.add(key)
                attractions.append(attraction)
        return attractions

    def _collect_hotels(self, days: List[DayPlan]) -> List[Hotel]:
        seen = set()
        hotels: List[Hotel] = []
        for day in days:
            if not day.hotel or not day.hotel.location:
                continue
            key = (
                day.hotel.name,
                round(day.hotel.location.longitude, 6),
                round(day.hotel.location.latitude, 6),
            )
            if key in seen:
                continue
            seen.add(key)
            hotels.append(copy.deepcopy(day.hotel))
        return hotels

    def _collect_meals(self, days: List[DayPlan]) -> List[Meal]:
        seen = set()
        meals: List[Meal] = []
        for day in days:
            for meal in day.meals:
                if not meal.location:
                    continue
                key = (
                    meal.type,
                    meal.name,
                    round(meal.location.longitude, 6),
                    round(meal.location.latitude, 6),
                )
                if key in seen:
                    continue
                seen.add(key)
                meals.append(copy.deepcopy(meal))
        return meals

    def _optimize_hotels_by_day_center(self, trip_plan: TripPlan, hotels: List[Hotel]) -> str:
        if not hotels:
            return "酒店缺少可计算坐标，暂未进行酒店位置同步优化。"

        changed_count = 0
        total_distance_km = 0.0
        matched_days = 0

        for day in trip_plan.days:
            center = self._day_center(day)
            if not center:
                continue

            hotel, distance_meters = self._nearest_hotel(center, hotels)
            if not hotel:
                continue

            matched_days += 1
            total_distance_km += distance_meters / 1000
            if not day.hotel or day.hotel.name != hotel.name:
                changed_count += 1
            day.hotel = copy.deepcopy(hotel)
            day.hotel.distance = f"距当天景点中心约 {distance_meters / 1000:.1f} 公里"

        if matched_days == 0:
            return "酒店位置未能匹配到有效的每日景点中心。"

        avg_distance_km = total_distance_km / matched_days
        return (
            f"已根据每日景点中心重新匹配酒店，{matched_days} 天完成酒店位置校准，"
            f"平均距当天景点中心约 {avg_distance_km:.1f} 公里，调整酒店 {changed_count} 次。"
        )

    def _day_center(self, day: DayPlan) -> Optional[Tuple[float, float]]:
        valid_attractions = [
            attraction
            for attraction in day.attractions
            if attraction.location
        ]
        if not valid_attractions:
            return None

        lon = sum(item.location.longitude for item in valid_attractions) / len(valid_attractions)
        lat = sum(item.location.latitude for item in valid_attractions) / len(valid_attractions)
        return lon, lat

    def _nearest_hotel(self, center: Tuple[float, float], hotels: List[Hotel]) -> Tuple[Optional[Hotel], float]:
        center_lon, center_lat = center
        best_hotel: Optional[Hotel] = None
        best_distance = float("inf")

        for hotel in hotels:
            if not hotel.location:
                continue
            distance = haversine_distance_meters(
                center_lon,
                center_lat,
                hotel.location.longitude,
                hotel.location.latitude,
            )
            if distance < best_distance:
                best_hotel = hotel
                best_distance = distance

        return best_hotel, best_distance

    def _optimize_meals_by_day_anchors(self, trip_plan: TripPlan, meals: List[Meal]) -> str:
        if not meals:
            return "餐饮缺少可计算坐标，暂未进行餐饮位置同步优化。"

        changed_count = 0
        matched_count = 0
        total_distance_km = 0.0

        for day in trip_plan.days:
            if not day.attractions:
                continue

            optimized_meals: List[Meal] = []
            used_names = set()
            for meal in day.meals:
                anchor = self._meal_anchor(day, meal.type)
                if not anchor:
                    optimized_meals.append(meal)
                    continue

                candidate, distance_meters = self._nearest_meal(anchor, meal.type, meals, used_names)
                if not candidate:
                    optimized_meals.append(meal)
                    continue

                matched_count += 1
                total_distance_km += distance_meters / 1000
                used_names.add(candidate.name)
                if meal.name != candidate.name:
                    changed_count += 1

                updated = copy.deepcopy(candidate)
                updated.description = self._append_distance_note(
                    updated.description,
                    f"距当日{self._meal_anchor_label(meal.type)}约 {distance_meters / 1000:.1f} 公里",
                )
                optimized_meals.append(updated)

            day.meals = optimized_meals

        if matched_count == 0:
            return "餐饮位置未能匹配到有效的每日用餐锚点。"

        avg_distance_km = total_distance_km / matched_count
        return (
            f"已按早餐靠近酒店/首个景点、午餐靠近中段景点、晚餐靠近末段景点的规则同步餐饮位置，"
            f"匹配餐饮 {matched_count} 次，平均距锚点约 {avg_distance_km:.1f} 公里，调整餐饮 {changed_count} 次。"
        )

    def _meal_anchor(self, day: DayPlan, meal_type: str) -> Optional[Tuple[float, float]]:
        if meal_type == "breakfast" and day.hotel and day.hotel.location:
            return day.hotel.location.longitude, day.hotel.location.latitude

        attractions = [item for item in day.attractions if item.location]
        if not attractions:
            return None

        if meal_type == "breakfast":
            attraction = attractions[0]
        elif meal_type == "lunch":
            attraction = attractions[len(attractions) // 2]
        elif meal_type == "dinner":
            attraction = attractions[-1]
        else:
            attraction = attractions[min(len(attractions) // 2, len(attractions) - 1)]

        return attraction.location.longitude, attraction.location.latitude

    def _nearest_meal(
        self,
        anchor: Tuple[float, float],
        meal_type: str,
        meals: List[Meal],
        used_names: set[str],
    ) -> Tuple[Optional[Meal], float]:
        anchor_lon, anchor_lat = anchor
        best_meal: Optional[Meal] = None
        best_distance = float("inf")

        same_type_meals = [
            meal
            for meal in meals
            if meal.location and meal.type == meal_type and meal.name not in used_names
        ]
        candidate_meals = same_type_meals or [
            meal
            for meal in meals
            if meal.location and meal.name not in used_names
        ]

        for meal in candidate_meals:
            distance = haversine_distance_meters(
                anchor_lon,
                anchor_lat,
                meal.location.longitude,
                meal.location.latitude,
            )
            if distance < best_distance:
                best_meal = meal
                best_distance = distance

        return best_meal, best_distance

    def _meal_anchor_label(self, meal_type: str) -> str:
        labels = {
            "breakfast": "酒店或首个景点",
            "lunch": "中段景点",
            "dinner": "末段景点",
            "snack": "中段景点",
        }
        return labels.get(meal_type, "行程锚点")

    def _append_distance_note(self, description: Optional[str], note: str) -> str:
        if not description:
            return note
        if note in description:
            return description
        return f"{description}（{note}）"

    def _apply_cached_order(self, trip_plan: TripPlan, cached: dict) -> None:
        by_name = {
            attraction.name: attraction
            for day in trip_plan.days
            for attraction in day.attractions
        }
        for index, names in enumerate(cached.get("days", [])):
            if index >= len(trip_plan.days):
                break
            trip_plan.days[index].attractions = [
                by_name[name]
                for name in names
                if name in by_name
            ]
            trip_plan.days[index].description = self._build_day_description(trip_plan.days[index], index)

    def _apply_cached_hotels(self, trip_plan: TripPlan, cached: dict, hotels: List[Hotel]) -> str:
        by_name = {hotel.name: hotel for hotel in hotels}
        changed_count = 0
        for index, hotel_name in enumerate(cached.get("hotels", [])):
            if index >= len(trip_plan.days) or not hotel_name or hotel_name not in by_name:
                continue
            current = trip_plan.days[index].hotel
            if not current or current.name != hotel_name:
                changed_count += 1
            trip_plan.days[index].hotel = copy.deepcopy(by_name[hotel_name])

        if not cached.get("hotels"):
            return self._optimize_hotels_by_day_center(trip_plan, hotels)
        return f"已复用缓存中的酒店匹配结果，调整酒店 {changed_count} 次。"

    def _apply_cached_meals(self, trip_plan: TripPlan, cached: dict, meals: List[Meal]) -> str:
        by_key = {(meal.type, meal.name): meal for meal in meals}
        changed_count = 0
        matched_count = 0

        for day_index, meal_keys in enumerate(cached.get("meals", [])):
            if day_index >= len(trip_plan.days):
                continue
            optimized_meals: List[Meal] = []
            for meal_type, meal_name in meal_keys:
                key = (meal_type, meal_name)
                if key not in by_key:
                    continue
                optimized_meals.append(copy.deepcopy(by_key[key]))
                matched_count += 1
            if optimized_meals:
                original_names = [meal.name for meal in trip_plan.days[day_index].meals]
                new_names = [meal.name for meal in optimized_meals]
                if original_names != new_names:
                    changed_count += 1
                trip_plan.days[day_index].meals = optimized_meals

        if not cached.get("meals"):
            return self._optimize_meals_by_day_anchors(trip_plan, meals)
        return f"已复用缓存中的餐饮匹配结果，匹配餐饮 {matched_count} 次，调整天数 {changed_count} 天。"

    def _build_day_description(self, day: DayPlan, index: int) -> str:
        names = "、".join(item.name for item in day.attractions[:3])
        return f"第 {index + 1} 天集中游览相近区域景点：{names}。"

    def _join_summary(self, *parts: str) -> str:
        return " ".join(part for part in parts if part)


_itinerary_optimizer = None


def get_itinerary_optimizer() -> ItineraryOptimizer:
    global _itinerary_optimizer

    if _itinerary_optimizer is None:
        _itinerary_optimizer = ItineraryOptimizer()

    return _itinerary_optimizer
