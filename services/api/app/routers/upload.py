# services/api/app/routers/upload.py

from fastapi import APIRouter, UploadFile, File

from core.services.file_ingest_service import ingest_file
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file → store locally → extract tables → insert rows → return file_id
    """
    try:
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        file_id = ingest_file(
            filename=file.filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

        return json_ok(
            {
                "file_id": file_id,
                "filename": file.filename,
                "content_type": content_type,
            }
        )
    except Exception as e:
        return json_error(str(e), status_code=500)
