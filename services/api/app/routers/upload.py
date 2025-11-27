from fastapi import APIRouter, UploadFile, File

from core.services.file_ingest_service import ingest_file
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        file_id = ingest_file(
            file.filename,
            file.content_type or "application/octet-stream",
            file_bytes
        )
        return json_ok({"file_id": file_id, "filename": file.filename})
    except Exception as e:
        return json_error(str(e), status_code=500)
