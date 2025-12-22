import uuid
from datetime import date
from sqlalchemy.orm import Session
from services.api.app.models import ChatSession, ChatMessage


def get_or_create_session(
    db: Session,
    *,
    user_id: str,
    chat_type: str,
    file_id: str | None = None,
):
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
            ChatSession.chat_type == chat_type,
            ChatSession.file_id == file_id,
            ChatSession.session_date == date.today(),
        )
        .first()
    )

    if session:
        return session

    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        chat_type=chat_type,
        file_id=file_id,
        session_date=date.today(),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def save_message(
    db: Session,
    *,
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    source: dict | None = None,
):
    msg = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=content,
        source=source,
    )

    db.add(msg)
    db.commit()
