from fastapi import APIRouter, HTTPException
from core.storage.postgres_client import execute
import fitz  # PyMuPDF
import json
import os
import requests
import pandas as pd

router = APIRouter()

# ------------------------------
# Mistral API config
# ------------------------------
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"


# ------------------------------------------------------
# Helper: Load extracted_rows into pandas DataFrame
# ------------------------------------------------------
def load_rows_df(file_id: str) -> pd.DataFrame:
    rows = execute(
        "SELECT id, table_name, row_data, created_at FROM extracted_rows WHERE file_id = %s",
        (file_id,)
    )

    if not rows:
        return pd.DataFrame()

    records = []
    for r in rows:
        try:
            row_json = r["row_data"]
        except:
            row_json = {}

        records.append({
            "id": r["id"],
            "table_name": r["table_name"],
            "created_at": r["created_at"],
            **row_json
        })

    return pd.DataFrame(records)


# ------------------------------------------------------
# GET /v1/files/{file_id}/text
# Extract plain text from PDF
# ------------------------------------------------------
@router.get("/v1/files/{file_id}/text")
async def get_file_text(file_id: str):
    # fetch file info
    file = execute(
        "SELECT storage_path, content_type FROM uploaded_files WHERE id = %s",
        (file_id,)
    )

    if not file:
        raise HTTPException(404, "File not found")

    file = file[0]
    file_path = file["storage_path"]
    content_type = file["content_type"]

    if content_type != "application/pdf":
        raise HTTPException(400, "Text extraction supported only for PDF")

    try:
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()

        return {"success": True, "data": text}

    except Exception as e:
        raise HTTPException(500, f"PDF extraction failed: {e}")


# ------------------------------------------------------
# /v1/analysis/summary
# Numeric summary
# ------------------------------------------------------
@router.get("/v1/analysis/summary")
async def summary_stats(file_id: str):
    df = load_rows_df(file_id)

    if df.empty:
        return {"success": True, "data": {}}

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return {"success": True, "data": {}}

    return {"success": True, "data": numeric_df.describe().to_dict()}


# ------------------------------------------------------
# /v1/analysis/descriptive
# Placeholder descriptive stats
# ------------------------------------------------------
@router.get("/v1/analysis/descriptive")
async def descriptive_stats(file_id: str, question: str):
    df = load_rows_df(file_id)

    return {
        "success": True,
        "data": f"Descriptive stats placeholder. Question: {question}, Rows: {len(df)}"
    }


# ------------------------------------------------------
# /v1/analysis/plots
# Histogram data
# ------------------------------------------------------
@router.get("/v1/analysis/plots")
async def histogram_plots(file_id: str):
    df = load_rows_df(file_id)

    if df.empty:
        return {"success": True, "data": {}}

    plots = {}
    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        counts = df[col].value_counts()
        plots[col] = {
            "bins": list(counts.index),
            "counts": list(counts.values)
        }

    return {"success": True, "data": plots}


# ------------------------------------------------------
# /v1/analysis/llm_summary  ← MISTRAL AI
# ------------------------------------------------------
@router.post("/v1/analysis/llm_summary")
async def llm_summary(payload: dict):

    text = payload.get("text", "")

    if not text:
        raise HTTPException(400, "No text provided")

    if not MISTRAL_API_KEY:
        raise HTTPException(500, "MISTRAL_API_KEY missing")

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
        "temperature": 0.4
    }

    try:
        res = requests.post(MISTRAL_ENDPOINT, headers=headers, json=body)
        res.raise_for_status()

        answer = res.json()["choices"][0]["message"]["content"]

        return {
            "success": True,
            "data": {
                "summary": answer
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Mistral API error: {e}")

