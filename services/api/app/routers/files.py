# services/api/app/routers/files.py

from fastapi import APIRouter, HTTPException
from core.storage.postgres_client import execute
from core.utils.response import json_ok, json_error
from core.utils.json_cleaner import clean_for_json
import fitz  # PyMuPDF

router = APIRouter(prefix="/v1/files", tags=["files"])


# ---------------------------------------------------------
# List uploaded files
# ---------------------------------------------------------
@router.get("")
def list_files():
    try:
        rows = execute(
            """
            SELECT id, filename, content_type, storage_path, created_at, doc_type
            FROM uploaded_files
            ORDER BY created_at DESC
            """
        )
        return json_ok(clean_for_json(rows))
    except Exception as e:
        return json_error(str(e), status_code=500)


# ---------------------------------------------------------
# Get extracted table rows
# ---------------------------------------------------------
@router.get("/{file_id}/rows")
def file_rows(file_id: str):
    try:
        rows = execute(
            """
            SELECT id, table_name, row_data, created_at
            FROM extracted_rows
            WHERE file_id = %s
            ORDER BY id ASC
            """,
            (file_id,)
        )
        return json_ok(clean_for_json(rows))
    except Exception as e:
        return json_error(str(e), status_code=500)


# ---------------------------------------------------------
# DELETE file
# ---------------------------------------------------------
@router.delete("/{file_id}")
def delete_file(file_id: str):
    try:
        execute("DELETE FROM uploaded_files WHERE id = %s", (file_id,))
        return json_ok({"deleted": file_id})
    except Exception as e:
        return json_error(str(e), status_code=500)


# ---------------------------------------------------------
# NEW: Extract raw text from PDF
# ---------------------------------------------------------
@router.get("/{file_id}/text")
def extract_text(file_id: str):
    """
    Extract full text from a PDF file.
    """
    try:
        # Fetch file info
        rows = execute(
            """
            SELECT storage_path, content_type 
            FROM uploaded_files
            WHERE id = %s
            """,
            (file_id,)
        )

        if not rows:
            raise HTTPException(status_code=404, detail="File not found")

        file = rows[0]
        file_path = file["storage_path"]
        content_type = file["content_type"]

        if content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF text extraction is supported")

        # Extract text
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()

        return json_ok({"text": text})

    except Exception as e:
        return json_error(str(e), status_code=500)
