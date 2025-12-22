from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import uuid

from services.api.app.db import get_db
from services.api.app.models import ChatSession, ChatMessage
from services.api.app.auth.deps import get_current_user
from core.utils.response import json_ok

router = APIRouter(prefix="/v1/chat", tags=["chat"])


# ---------------------------------------
# GET ALL CHAT SESSIONS (SIDEBAR)
# ---------------------------------------
@router.get("/sessions")
def list_sessions(
    chat_type: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(ChatSession).filter(ChatSession.user_id == user["id"])

    if chat_type:
        q = q.filter(ChatSession.chat_type == chat_type)

    sessions = q.order_by(ChatSession.created_at.desc()).all()

    return json_ok([
        {
            "id": str(s.id),
            "title": s.title or "New Chat",
            "chat_type": s.chat_type,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ])


# ---------------------------------------
# CREATE NEW CHAT SESSION
# ---------------------------------------
@router.post("/sessions")
def create_session(
    chat_type: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user["id"],
        chat_type=chat_type,
        session_date=date.today(),
        title="New Chat",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return json_ok({"session_id": str(session.id)})


# ---------------------------------------
# GET MESSAGES
# ---------------------------------------
@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user["id"],
        )
        .first()
    )

    if not session:
        raise HTTPException(404, "Chat not found")

    return json_ok([
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in session.messages
    ])


# ---------------------------------------
# DELETE CHAT
# ---------------------------------------
@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user["id"],
        )
        .first()
    )

    if not session:
        raise HTTPException(404, "Chat not found")

    db.delete(session)
    db.commit()
    return json_ok({"deleted": session_id})
