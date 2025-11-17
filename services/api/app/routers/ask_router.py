from fastapi import APIRouter, Depends
from app.schemas.ask import AskRequest, AskResponse
from app.schemas.responses import ResponseEnvelope
from core.services.query_service import answer_query

router = APIRouter(prefix="/v1", tags=["ask"])


def auth_user():
    """
    TODO: replace with real authentication.
    For now, returns a demo user_id.
    """
    return {"user_id": "demo-user"}


@router.post("/ask", response_model=ResponseEnvelope)
def ask_api(payload: AskRequest, user=Depends(auth_user)):
    """
    Main RAG endpoint.
    """
    response_data = answer_query(
        query=payload.query,
        top_k=payload.top_k,
        user_id=user["user_id"]
    )

    return ResponseEnvelope(
        success=True,
        data=AskResponse(**response_data)
    )

