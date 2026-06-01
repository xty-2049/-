"""Trip planning API routes."""

from fastapi import APIRouter, HTTPException

from ...agents.trip_planner_agent import get_trip_planner_agent
from ...models.schemas import (
    TripConfirmRequest,
    TripPlanResponse,
    TripRequest,
    TripRevisionRequest,
)
from ...services.session_service import get_trip_session_store

router = APIRouter(prefix="/trip", tags=["trip-planning"])


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="Generate a trip plan",
    description="Generate the first itinerary and create a temporary editing session.",
)
async def plan_trip(request: TripRequest):
    try:
        agent = get_trip_planner_agent()
        trip_plan = agent.plan_trip(request)
        session = get_trip_session_store().create(request, trip_plan)

        return TripPlanResponse(
            success=True,
            message="旅行方案已生成，可以继续修改",
            data=trip_plan,
            session_id=session.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成旅行方案失败: {str(e)}")


@router.post(
    "/revise",
    response_model=TripPlanResponse,
    summary="Revise an active trip plan",
    description="Revise the current plan in a temporary session using a natural-language request.",
)
async def revise_trip(request: TripRevisionRequest):
    store = get_trip_session_store()
    session = store.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话已结束或已过期，请重新生成旅行方案")

    try:
        agent = get_trip_planner_agent()
        revised_plan = agent.revise_trip(
            current_plan=session.current_plan,
            user_message=request.message,
            request=session.original_request,
        )
        store.update_plan(request.session_id, revised_plan, request.message)

        return TripPlanResponse(
            success=True,
            message="旅行方案已根据你的要求更新",
            data=revised_plan,
            session_id=request.session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改旅行方案失败: {str(e)}")


@router.post(
    "/confirm",
    response_model=TripPlanResponse,
    summary="Confirm and close a trip session",
    description="Delete the temporary session after the user confirms the plan.",
)
async def confirm_trip(request: TripConfirmRequest):
    removed = get_trip_session_store().delete(request.session_id)
    return TripPlanResponse(
        success=True,
        message="旅行方案已确认，会话已结束" if removed else "会话已经不存在",
        data=None,
        session_id=None,
    )


@router.get("/health", summary="Trip planner health check")
async def health_check():
    agent = get_trip_planner_agent()
    return {
        "status": "healthy",
        "service": "trip-planner",
        "agents": {
            "attraction": len(agent.attraction_agent.list_tools()),
            "weather": len(agent.weather_agent.list_tools()),
            "hotel": len(agent.hotel_agent.list_tools()),
            "planner": len(agent.planner_agent.list_tools()),
        },
    }
