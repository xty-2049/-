"""SQLite cache for external map and planning data."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


class CacheService:
    """Small persistent cache used to avoid repeated external API calls."""

    def __init__(self, db_path: Optional[Path] = None):
        backend_dir = Path(__file__).resolve().parents[2]
        self.db_path = db_path or backend_dir / "data" / "trip_cache.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    namespace TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    PRIMARY KEY (namespace, cache_key)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at ON api_cache(expires_at)"
            )

    def build_key(self, *parts: Any) -> str:
        raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, namespace: str, key: str) -> Optional[Any]:
        now = int(time.time())
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value FROM api_cache
                WHERE namespace = ? AND cache_key = ? AND expires_at > ?
                """,
                (namespace, key, now),
            ).fetchone()

        if not row:
            return None
        return json.loads(row[0])

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: int = 86400) -> None:
        now = int(time.time())
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO api_cache
                    (namespace, cache_key, value, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (namespace, key, payload, now, now + ttl_seconds),
            )

    def get_or_set(self, namespace: str, key: str, producer, ttl_seconds: int = 86400) -> Any:
        cached = self.get(namespace, key)
        if cached is not None:
            return cached

        value = producer()
        self.set(namespace, key, value, ttl_seconds)
        return value

    def clear_expired(self) -> int:
        now = int(time.time())
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM api_cache WHERE expires_at <= ?", (now,))
            return cursor.rowcount


_cache_service = None


def get_cache_service() -> CacheService:
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService()

    return _cache_service
