# app/schemas/files.py
from datetime import datetime
from typing import List, Any
from pydantic import BaseModel
from uuid import UUID


class UploadedFileOut(BaseModel):
    id: UUID
    filename: str
    content_type: str
    created_at: datetime

    class Config:
        orm_mode = True


class ExtractedRowOut(BaseModel):
    id: int
    file_id: UUID
    table_name: str | None
    row_data: dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
