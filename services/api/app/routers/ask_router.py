from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
import requests
import uuid
from datetime import date
from services.api.app.chat.utils import get_or_create_session, save_message
from services.api.app.db import get_db
from services.api.app.schemas.ask import AskRequest
from services.api.app.models import (
    ExtractedText,
    ExtractedRow,
    UploadedFile,
    ChatSession,
    ChatMessage,
)
from services.api.app.auth.deps import get_current_user
from core.services.query_service import answer_query
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1", tags=["ask"])


# ============================================================
# GLOBAL RAG CHAT (AUTHENTICATED + PERSISTENT CHAT)
# ============================================================
@router.post("/ask")
def ask_api(
    payload: AskRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        user_id = str(user["id"])

        # 1️⃣ Get or create chat session
        session = get_or_create_session(
            db=db,
            user_id=user_id,
            chat_type="rag",
        )

        # 2️⃣ Save user message
        save_message(
            db=db,
            session_id=session.id,
            user_id=user_id,
            role="user",
            content=payload.query,
        )

        # 3️⃣ Generate answer
        result = answer_query(
            query=payload.query,
            top_k=payload.top_k,
            user_id=user_id,
        )

        answer = result.get("answer", "")

        # 4️⃣ Save assistant message
        save_message(
            db=db,
            session_id=session.id,
            user_id=user_id,
            role="assistant",
            content=answer,
            source=result.get("citations"),
        )

        return json_ok({
            "answer": answer,
            "session_id": str(session.id),
        })

    except Exception as e:
        return json_error(str(e), 500)


# ============================================================
# FILE-SCOPED CHAT (AUTHENTICATED + OWNED)
# ============================================================

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"


@router.post("/ask/file/{file_id}")
def ask_file_api(
    file_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        question = payload.get("question", "").strip()
        if not question:
            return json_error("Question is required", 400)

        user_id = str(user["id"])

        # --------------------------------------------------
        # Verify file ownership
        # --------------------------------------------------
        file = (
            db.query(UploadedFile)
            .filter(
                UploadedFile.id == file_id,
                UploadedFile.user_id == user_id,
            )
            .first()
        )

        if not file:
            return json_error("File not found", 404)

        # --------------------------------------------------
        # Load extracted text
        # --------------------------------------------------
        text_obj = (
            db.query(ExtractedText)
            .filter(
                ExtractedText.file_id == file_id,
                ExtractedText.user_id == user_id,
            )
            .first()
        )

        file_text = text_obj.text if text_obj else ""

        # --------------------------------------------------
        # Load extracted rows
        # --------------------------------------------------
        rows = (
            db.query(ExtractedRow)
            .filter(
                ExtractedRow.file_id == file_id,
                ExtractedRow.user_id == user_id,
            )
            .all()
        )

        table_lines = []
        for row in rows:
            row_str = ", ".join(
                f"{k}: {v}" for k, v in (row.row_data or {}).items()
            )
            table_lines.append(f"[{row.table_name}] {row_str}")

        table_text = "\n".join(table_lines)

        final_context = f"""
===== DOCUMENT TEXT =====
{file_text}

===== TABLES =====
{table_text}
""".strip()

        if not final_context:
            return json_error("No extracted content found", 404)

        # --------------------------------------------------
        # Mistral request
        # --------------------------------------------------
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }

        prompt = (
            "Answer ONLY from the provided document context.\n\n"
            f"CONTEXT:\n{final_context}\n\n"
            f"QUESTION:\n{question}"
        )

        body = {
            "model": MISTRAL_MODEL,
            "messages": [
                {"role": "system", "content": "Use only the given context."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        res = requests.post(
            MISTRAL_ENDPOINT,
            headers=headers,
            json=body,
            timeout=60,
        )
        res.raise_for_status()

        answer = res.json()["choices"][0]["message"]["content"]

        return json_ok({"answer": answer})

    except Exception as e:
        return json_error(f"Mistral API failure: {e}", 500)
