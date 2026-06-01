"""Temporary in-memory trip planning sessions."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models.schemas import TripPlan, TripRequest


@dataclass
class TripSession:
    session_id: str
    original_request: TripRequest
    current_plan: TripPlan
    messages: List[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class TripSessionStore:
    """Keeps active planning sessions only for the current backend process."""

    def __init__(self, ttl_seconds: int = 30 * 60):
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, TripSession] = {}

    def create(self, request: TripRequest, plan: TripPlan) -> TripSession:
        self.cleanup_expired()
        session_id = uuid.uuid4().hex
        session = TripSession(
            session_id=session_id,
            original_request=request,
            current_plan=plan,
            messages=[
                {
                    "role": "user",
                    "content": "Initial trip request",
                    "payload": request.model_dump(),
                },
                {
                    "role": "assistant",
                    "content": "Initial trip plan generated",
                },
            ],
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[TripSession]:
        self.cleanup_expired()
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.updated_at = time.time()
        return session

    def update_plan(self, session_id: str, plan: TripPlan, user_message: str) -> Optional[TripSession]:
        session = self.get(session_id)
        if not session:
            return None
        session.current_plan = plan
        session.updated_at = time.time()
        session.messages.append({"role": "user", "content": user_message})
        session.messages.append({"role": "assistant", "content": "Trip plan revised"})
        return session

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def cleanup_expired(self) -> int:
        now = time.time()
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.updated_at > self.ttl_seconds
        ]
        for session_id in expired_ids:
            self._sessions.pop(session_id, None)
        return len(expired_ids)


_trip_session_store = TripSessionStore()


def get_trip_session_store() -> TripSessionStore:
    return _trip_session_store
