from fastapi import APIRouter
from core.storage.postgres_client import execute
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1/files", tags=["files"])

@router.get("")
def list_files():   # ❗ REMOVE response_model
    rows = execute("""
        SELECT id, filename, content_type, storage_path, created_at
        FROM uploaded_files
        ORDER BY created_at DESC
    """)
    return json_ok(rows)

@router.get("/{file_id}/rows")
def file_rows(file_id: str):  # ❗ REMOVE response_model
    rows = execute("""
        SELECT id, table_name, row_data, created_at
        FROM extracted_rows
        WHERE file_id=%s
        ORDER BY id ASC
    """, (file_id,))
    return json_ok(rows)

@router.delete("/{file_id}")
def delete_file(file_id: str):
    execute("DELETE FROM uploaded_files WHERE id=%s", (file_id,))
    return json_ok({"deleted": file_id})
