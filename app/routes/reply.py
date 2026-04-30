"""
POST /v1/reply — Generate final deterministic merchant-facing message.
Anti-repeat: same context_id + same hash = cached message returned.
"""
import logging
import time
from fastapi import APIRouter, HTTPException
from app.schemas.context_schema import ReplyRequest
from app.engine.scorer import score_context
from app.engine.renderer import build_render_context, render_message, message_hash
from app.storage.store import ContextStore

router = APIRouter(tags=["Engine"])
logger = logging.getLogger(__name__)


@router.post("/reply")
def post_reply(request: ReplyRequest):
    store = ContextStore.get_instance()
    state = store.get_state(request.context_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No context found for context_id='{request.context_id}'. "
                   "POST /v1/context first.",
        )

    merchant_data = state.merchant.data if state.merchant else {}
    trigger_data  = state.trigger.data  if state.trigger  else {}
    customer_data = state.customer.data if state.customer else {}

    category = merchant_data.get("category", "restaurant")

   
    if state.last_tick_result:
        action = state.last_tick_result["action"]
        score  = state.last_tick_result["score"]
    else:
        result = score_context(request.context_id)
        action = result.action
        score  = result.total

    if action == "no_action":
        return {
            "context_id": request.context_id,
            "action": action,
            "message": None,
            "reason": "Score too low or cooldown active. No message generated.",
        }

    render_ctx = build_render_context(merchant_data, trigger_data, customer_data)
    message = render_message(category, action, score, render_ctx)
    msg_hash = message_hash(message)

   
    is_repeat = msg_hash in state.message_hashes
    if is_repeat:
        logger.info(
            "Repeat message detected for context_id=%s hash=%s — returning cached",
            request.context_id, msg_hash,
        )
        return {
            "context_id": request.context_id,
            "action": action,
            "message": message,
            "message_hash": msg_hash,
            "score": score,
            "char_count": len(message),
            "repeat": True,
            "note": "This message was already sent. Update context to get a fresh message.",
        }

   
    if not request.dry_run:
        store.record_message_sent(request.context_id, msg_hash, time.time())
        logger.info(
            "Message generated and persisted: context_id=%s action=%s chars=%d",
            request.context_id, action, len(message),
        )

    return {
        "context_id": request.context_id,
        "action": action,
        "message": message,
        "message_hash": msg_hash,
        "score": score,
        "char_count": len(message),
        "repeat": False,
        "dry_run": request.dry_run,
    }
