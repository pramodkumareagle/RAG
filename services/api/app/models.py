# app/models.py
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from services.api.app.db import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    doc_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rows = relationship("ExtractedRow", back_populates="file", cascade="all, delete-orphan")


class ExtractedRow(Base):
    __tablename__ = "extracted_rows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    table_name = Column(String, nullable=True)  # sheet name, table index, etc.
    row_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("UploadedFile", back_populates="rows")



class ExtractedText(Base):
    __tablename__ = "extracted_text"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id", ondelete="CASCADE"))
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("UploadedFile", backref="extracted_text_entries")

