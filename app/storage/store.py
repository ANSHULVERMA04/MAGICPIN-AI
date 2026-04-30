"""
In-memory context store with conflict-safe versioning.
Singleton pattern; swap out backend adapter for Redis in production.
"""
from __future__ import annotations
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


COOLDOWN_SECONDS = 3600  


class ContextRecord:
    """Holds versioned data for a single scope within a context_id."""

    def __init__(self, version: int, data: Dict[str, Any]):
        self.version = version
        self.data = data


class MerchantState:
    """
    Aggregated runtime state for a context_id across all scopes.
    Includes the last computed tick result and cooldown tracking.
    """

    def __init__(self):
        self.merchant: Optional[ContextRecord] = None
        self.trigger: Optional[ContextRecord] = None
        self.customer: Optional[ContextRecord] = None
        self.last_tick_result: Optional[Dict[str, Any]] = None
        self.last_message_at: Optional[float] = None  # unix timestamp
        self.message_hashes: set[str] = set()  # anti-repeat hashes


class ContextStore:
    """Thread-safe singleton in-memory store."""

    _instance: Optional["ContextStore"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._data: Dict[str, MerchantState] = {}
        self._rw_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "ContextStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

  

    def upsert_context(
        self,
        context_id: str,
        scope: str,
        version: int,
        data: Dict[str, Any],
    ) -> str:
        """
        Returns:
            "inserted"  — new record stored
            "updated"   — higher version replaced existing
            "no_op"     — same version already present (idempotent)
            "ignored"   — lower version rejected
        """
        with self._rw_lock:
            if context_id not in self._data:
                self._data[context_id] = MerchantState()

            state = self._data[context_id]
            existing: Optional[ContextRecord] = getattr(state, scope)

            if existing is None:
                setattr(state, scope, ContextRecord(version, data))
                logger.info("context_id=%s scope=%s inserted v%d", context_id, scope, version)
                return "inserted"

            if version == existing.version:
                logger.debug("context_id=%s scope=%s v%d no-op", context_id, scope, version)
                return "no_op"

            if version > existing.version:
                setattr(state, scope, ContextRecord(version, data))
                logger.info("context_id=%s scope=%s updated v%d→v%d", context_id, scope, existing.version, version)
                return "updated"

            logger.warning(
                "context_id=%s scope=%s rejected stale v%d (current v%d)",
                context_id, scope, version, existing.version,
            )
            return "ignored"

  

    def get_state(self, context_id: str) -> Optional[MerchantState]:
        with self._rw_lock:
            return self._data.get(context_id)

    def save_tick_result(self, context_id: str, result: Dict[str, Any]) -> None:
        with self._rw_lock:
            state = self._data.get(context_id)
            if state:
                state.last_tick_result = result

    def record_message_sent(self, context_id: str, msg_hash: str, timestamp: float) -> None:
        with self._rw_lock:
            state = self._data.get(context_id)
            if state:
                state.last_message_at = timestamp
                state.message_hashes.add(msg_hash)

    def count(self) -> int:
        with self._rw_lock:
            return len(self._data)

    def all_context_ids(self) -> list[str]:
        with self._rw_lock:
            return list(self._data.keys())
