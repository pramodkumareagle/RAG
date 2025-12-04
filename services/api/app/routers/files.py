# services/api/app/routers/files.py

from fastapi import APIRouter

from core.storage.postgres_client import execute
from core.utils.response import json_ok, json_error
from core.utils.json_cleaner import clean_for_json

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("")
def list_files():
    """
    List all uploaded files with basic metadata.
    """
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


@router.get("/{file_id}/rows")
def file_rows(file_id: str):
    """
    List all extracted rows for a given file.
    """
    try:
        rows = execute(
            """
            SELECT id, table_name, row_data, created_at
            FROM extracted_rows
            WHERE file_id = %s
            ORDER BY id ASC
            """,
            (file_id,),
        )
        return json_ok(clean_for_json(rows))
    except Exception as e:
        return json_error(str(e), status_code=500)


@router.delete("/{file_id}")
def delete_file(file_id: str):
    """
    Delete a file and its extracted rows.
    """
    try:
        execute("DELETE FROM uploaded_files WHERE id = %s", (file_id,))
        return json_ok({"deleted": file_id})
    except Exception as e:
        return json_error(str(e), status_code=500)
