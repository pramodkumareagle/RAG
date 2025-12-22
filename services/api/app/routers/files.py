from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from services.api.app.db import get_db
from services.api.app.models import UploadedFile, ExtractedRow, ExtractedText
from services.api.app.auth.deps import get_current_user
from core.utils.response import json_ok, json_error

router = APIRouter(prefix="/v1/files", tags=["files"])


# ---------------------------------------------------------
# GET ALL UPLOADED FILES (USER-SCOPED)
# ---------------------------------------------------------
@router.get("")
def list_files(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        user_id = str(user["id"])

        files = (
            db.query(UploadedFile)
            .filter(UploadedFile.user_id == user_id)
            .order_by(UploadedFile.created_at.desc())
            .all()
        )

        result = [
            {
                "id": str(f.id),
                "filename": f.filename,
                "doc_type": f.doc_type,
                "content_type": f.content_type,
                "storage_path": f.storage_path,
                "created_at": f.created_at.isoformat(),
            }
            for f in files
        ]

        return json_ok(result)

    except Exception as e:
        return json_error(str(e))


# ---------------------------------------------------------
# GET TABLE ROWS FOR A FILE (OWNED)
# ---------------------------------------------------------
@router.get("/{file_id}/rows")
def file_rows(
    file_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        user_id = str(user["id"])

        # 🔐 verify ownership
        file = (
            db.query(UploadedFile)
            .filter(
                UploadedFile.id == file_id,
                UploadedFile.user_id == user_id,
            )
            .first()
        )

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        rows = (
            db.query(ExtractedRow)
            .filter(
                ExtractedRow.file_id == file_id,
                ExtractedRow.user_id == user_id,
            )
            .order_by(ExtractedRow.id.asc())
            .all()
        )

        result = [
            {
                "id": r.id,
                "table_name": r.table_name,
                "row_data": r.row_data,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]

        return json_ok(result)

    except HTTPException:
        raise
    except Exception as e:
        return json_error(str(e))


# ---------------------------------------------------------
# GET EXTRACTED TEXT (OWNED)
# ---------------------------------------------------------
@router.get("/{file_id}/text")
def get_file_text(
    file_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        user_id = str(user["id"])

        # 🔐 verify ownership
        file = (
            db.query(UploadedFile)
            .filter(
                UploadedFile.id == file_id,
                UploadedFile.user_id == user_id,
            )
            .first()
        )

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        text_record = (
            db.query(ExtractedText)
            .filter(ExtractedText.file_id == file_id)
            .order_by(ExtractedText.id.asc())
            .first()
        )

        if not text_record:
            return json_ok({"text": ""})

        return json_ok({"text": text_record.text})

    except HTTPException:
        raise
    except Exception as e:
        return json_error(str(e))


# ---------------------------------------------------------
# DELETE FILE (OWNED, SAFE)
# ---------------------------------------------------------
@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        user_id = str(user["id"])

        file_obj = (
            db.query(UploadedFile)
            .filter(
                UploadedFile.id == file_id,
                UploadedFile.user_id == user_id,
            )
            .first()
        )

        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")

        # 🧹 delete physical file
        try:
            if file_obj.storage_path and os.path.exists(file_obj.storage_path):
                os.remove(file_obj.storage_path)
        except Exception as e:
            print("⚠️ File delete error:", e)

        # 🧨 cascade deletes ExtractedRow & ExtractedText
        db.delete(file_obj)
        db.commit()

        return json_ok({"deleted": file_id})

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return json_error(str(e))
