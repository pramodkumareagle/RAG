# services/api/app/routers/ask_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import requests

from services.api.app.db import get_db
from services.api.app.schemas.ask import AskRequest
from services.api.app.models import ExtractedText, ExtractedRow
from core.services.query_service import answer_query
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1", tags=["ask"])


def auth_user():
    return {"user_id": "demo-user"}


# --------------------------------------------
# GLOBAL RAG (existing)
# --------------------------------------------
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


# --------------------------------------------
# NEW ENDPOINT — Chat ONLY with one file
# --------------------------------------------

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"


@router.post("/ask/file/{file_id}")
def ask_file_api(file_id: str, payload: dict, db: Session = Depends(get_db)):
    """
    Chat ONLY with one uploaded document.
    Uses extracted text + extracted rows from this file.
    """
    question = payload.get("question", "").strip()
    if not question:
        return json_error("Question is required", 400)

    # ----------------------------
    # Load extracted full text
    # ----------------------------
    text_obj = (
        db.query(ExtractedText)
        .filter(ExtractedText.file_id == file_id)
        .first()
    )
    file_text = text_obj.text if text_obj else ""

    # ----------------------------
    # Load table rows
    # ----------------------------
    rows = (
        db.query(ExtractedRow)
        .filter(ExtractedRow.file_id == file_id)
        .all()
    )

    table_lines = []
    for row in rows:
        row_str = ", ".join([f"{k}: {v}" for k, v in row.row_data.items()])
        table_lines.append(f"[{row.table_name}] {row_str}")

    table_text = "\n".join(table_lines)

    # ----------------------------
    # Ensure we have content
    # ----------------------------
    final_context = f"""
===== DOCUMENT TEXT =====
{file_text}

===== TABLES =====
{table_text}
"""

    if not final_context.strip():
        return json_error("This file has no extracted text or tables", 404)

    # ----------------------------
    # Prepare Mistral request
    # ----------------------------
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = (
        "You are an AI assistant. You MUST answer ONLY based on the provided "
        "document content. Do NOT add external facts.\n\n"
        f"CONTEXT:\n{final_context}\n\n"
        f"QUESTION: {question}"
    )

    body = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": "You answer ONLY using provided context."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    try:
        res = requests.post(MISTRAL_ENDPOINT, headers=headers, json=body)
        res.raise_for_status()
        answer = res.json()["choices"][0]["message"]["content"]
        return json_ok({"answer": answer})

    except Exception as e:
        return json_error(f"Mistral API failure: {e}", 500)
