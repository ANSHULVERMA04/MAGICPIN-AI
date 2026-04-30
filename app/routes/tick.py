"""
POST /v1/tick — Evaluate context, run scoring engine, select best action, persist state.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.context_schema import TickRequest
from app.engine.scorer import score_context
from app.storage.store import ContextStore

router = APIRouter(tags=["Engine"])
logger = logging.getLogger(__name__)


@router.post("/tick")
def post_tick(request: TickRequest):
    store = ContextStore.get_instance()
    state = store.get_state(request.context_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No context found for context_id='{request.context_id}'. "
                   "POST /v1/context first.",
        )

   
    result = score_context(request.context_id)

    tick_result = {
        "context_id": request.context_id,
        "action": result.action,
        "score": result.total,
        "components": result.components,
        "rationale": result.rationale,
    }

    store.save_tick_result(request.context_id, tick_result)
    logger.info("Tick complete: context_id=%s action=%s score=%.1f",
                request.context_id, result.action, result.total)

    return tick_result
