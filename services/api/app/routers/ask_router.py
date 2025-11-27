from fastapi import APIRouter, Depends

from services.api.app.schemas.ask import AskRequest
from core.services.query_service import answer_query
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1", tags=["ask"])


def auth_user():
    return {"user_id": "demo-user"}


@router.post("/ask")
def ask_api(payload: AskRequest, user=Depends(auth_user)):
    try:
        result = answer_query(
            query=payload.query,
            top_k=payload.top_k,
            user_id=user["user_id"],
        )
        return json_ok(result)
    except Exception as e:
        return json_error(str(e), status_code=500)
