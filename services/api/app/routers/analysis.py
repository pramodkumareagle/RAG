from fastapi import APIRouter, HTTPException, Depends
from core.storage.postgres_client import execute
import fitz  # PyMuPDF
import os
import requests
import pandas as pd

from services.api.app.auth.deps import get_current_user  # ✅ add this

router = APIRouter()

# ------------------------------
# Mistral API config
# ------------------------------
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"


# ------------------------------------------------------
# Helper: verify file belongs to user
# ------------------------------------------------------
def get_owned_file_or_404(file_id: str, user_id: str):
    rows = execute(
        """
        SELECT id, storage_path, content_type, doc_type, filename
        FROM uploaded_files
        WHERE id = %s AND user_id = %s
        """,
        (file_id, user_id),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="File not found")
    return rows[0]


# ------------------------------------------------------
# Helper: Load extracted_rows into pandas DataFrame (scoped to user)
# ------------------------------------------------------
def load_rows_df(file_id: str, user_id: str) -> pd.DataFrame:
    rows = execute(
        """
        SELECT id, table_name, row_data, created_at
        FROM extracted_rows
        WHERE file_id = %s AND user_id = %s
        ORDER BY id ASC
        """,
        (file_id, user_id),
    )

    if not rows:
        return pd.DataFrame()

    records = []
    for r in rows:
        row_json = r.get("row_data") or {}
        records.append(
            {
                "id": r.get("id"),
                "table_name": r.get("table_name"),
                "created_at": r.get("created_at"),
                **row_json,
            }
        )

    return pd.DataFrame(records)


# ------------------------------------------------------
# GET /v1/files/{file_id}/text
# Extract plain text from PDF (owned by user)
# ------------------------------------------------------
@router.get("/v1/files/{file_id}/text")
async def get_file_text(file_id: str, user=Depends(get_current_user)):
    file = get_owned_file_or_404(file_id=file_id, user_id=str(user["id"]))

    file_path = file["storage_path"]
    content_type = file["content_type"]

    if content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Text extraction supported only for PDF")

    try:
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()

        return {"success": True, "data": {"text": text}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {e}")


# ------------------------------------------------------
# /v1/analysis/summary
# Numeric summary (owned by user)
# ------------------------------------------------------
@router.get("/v1/analysis/summary")
async def summary_stats(file_id: str, user=Depends(get_current_user)):
    # ensures file belongs to user
    _ = get_owned_file_or_404(file_id=file_id, user_id=str(user["id"]))

    df = load_rows_df(file_id, user_id=str(user["id"]))
    if df.empty:
        return {"success": True, "data": {}}

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {"success": True, "data": {}}

    return {"success": True, "data": numeric_df.describe().to_dict()}


# ------------------------------------------------------
# /v1/analysis/descriptive
# Placeholder descriptive stats (owned by user)
# ------------------------------------------------------
@router.get("/v1/analysis/descriptive")
async def descriptive_stats(file_id: str, question: str, user=Depends(get_current_user)):
    _ = get_owned_file_or_404(file_id=file_id, user_id=str(user["id"]))

    df = load_rows_df(file_id, user_id=str(user["id"]))
    return {
        "success": True,
        "data": f"Descriptive stats placeholder. Question: {question}, Rows: {len(df)}",
    }


# ------------------------------------------------------
# /v1/analysis/plots
# Histogram data (owned by user)
# ------------------------------------------------------
@router.get("/v1/analysis/plots")
async def histogram_plots(file_id: str, user=Depends(get_current_user)):
    _ = get_owned_file_or_404(file_id=file_id, user_id=str(user["id"]))

    df = load_rows_df(file_id, user_id=str(user["id"]))
    if df.empty:
        return {"success": True, "data": {}}

    plots = {}
    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        counts = df[col].value_counts()
        plots[col] = {
            "bins": list(counts.index),
            "counts": list(counts.values),
        }

    return {"success": True, "data": plots}


# ------------------------------------------------------
# /v1/analysis/llm_summary  ← MISTRAL AI (auth required)
# Note: this is text-based, so we just protect it; it doesn't need file ownership
# ------------------------------------------------------
@router.post("/v1/analysis/llm_summary")
async def llm_summary(payload: dict, user=Depends(get_current_user)):
    text = (payload or {}).get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY missing")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": "You are a document analysis assistant."},
            {
                "role": "user",
                "content": (
                    "Summarize this document.\n\n"
                    "Return a clean structured summary.\n\n"
                    f"Document:\n{text}"
                ),
            },
        ],
        "temperature": 0.4,
    }

    try:
        res = requests.post(MISTRAL_ENDPOINT, headers=headers, json=body, timeout=60)
        res.raise_for_status()
        answer = res.json()["choices"][0]["message"]["content"]

        return {"success": True, "data": {"summary": answer}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mistral API error: {e}")
