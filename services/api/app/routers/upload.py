import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from services.api.app.db import get_db
from services.api.app.models import UploadedFile
from services.api.app.auth.deps import get_current_user

from core.services.universal_extractor import extract_anything
from core.services.file_ingest_service import ingest_file
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1/upload", tags=["upload"])

# -------------------------------------------------
# Storage dir
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.normpath(os.path.join(BASE_DIR, "../../../storage"))
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upload any document type → Extract text/tables → Classify → Save to DB.
    """
    try:
        user_id = str(user["id"])

        # ---------------------------------------------
        # Read binary data
        # ---------------------------------------------
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        # ---------------------------------------------
        # Generate UUID
        # ---------------------------------------------
        file_id = uuid.uuid4()

        # ---------------------------------------------
        # Save raw file to disk
        # ---------------------------------------------
        disk_name = f"{file_id}_{file.filename}"
        storage_path = os.path.join(STORAGE_DIR, disk_name)

        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # ---------------------------------------------
        # Universal extraction
        # ---------------------------------------------
        extraction = extract_anything(
            filename=file.filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

        full_text = extraction.get("text", "")
        tables = extraction.get("tables", [])
        doc_type = extraction.get("doc_type", "unknown")

        # ---------------------------------------------
        # Save file metadata (USER OWNED)
        # ---------------------------------------------
        new_file = UploadedFile(
            id=file_id,
            user_id=user_id,  # 🔐 IMPORTANT
            filename=file.filename,
            content_type=content_type,
            storage_path=storage_path,
            doc_type=doc_type,
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        # ---------------------------------------------
        # Save extracted text + tables (USER OWNED)
        # ---------------------------------------------
        ingest_file(
            db=db,
            file_id=str(file_id),
            user_id=user_id,  # 🔐 IMPORTANT
            extracted_text=full_text,
            extracted_tables=tables,
        )

        return json_ok(
            {
                "file_id": str(file_id),
                "filename": new_file.filename,
                "doc_type": doc_type,
                "content_type": content_type,
                "storage_path": new_file.storage_path,
            }
        )

    except Exception as e:
        db.rollback()
        return json_error(str(e), status_code=500)
