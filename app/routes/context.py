"""
POST /v1/context — Accept and version-safely store context updates.
"""
import logging
from fastapi import APIRouter
from app.schemas.context_schema import ContextPayload
from app.storage.store import ContextStore

router = APIRouter(tags=["Context"])
logger = logging.getLogger(__name__)


@router.post("/context")
def post_context(payload: ContextPayload):
    store = ContextStore.get_instance()

    
    scope_map = {
        "merchant": payload.merchant,
        "trigger":  payload.trigger,
        "customer": payload.customer,
    }
    scope_obj = scope_map[payload.scope]
    data = scope_obj.model_dump() if scope_obj else {}

    result = store.upsert_context(
        context_id=payload.context_id,
        scope=payload.scope,
        version=payload.version,
        data=data,
    )

    return {
        "context_id": payload.context_id,
        "scope": payload.scope,
        "version": payload.version,
        "result": result,
    }
