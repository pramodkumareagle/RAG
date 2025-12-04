# core/services/file_ingest_service.py

import os
import uuid
import datetime as _dt
from typing import List, Tuple, Dict, Any

import pandas as pd
from psycopg2.extras import Json

from core.storage.postgres_client import execute
from core.services.document_classifier import classify_document
from core.services.text_extractor import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_via_ocr,
)
import pdfplumber


RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "./data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)


# -------------------------------------------------------
# Save file locally
# -------------------------------------------------------
def save_uploaded_file(filename: str, file_bytes: bytes) -> str:
    unique_name = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(RAW_DATA_DIR, unique_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


# -------------------------------------------------------
# PDF table extractor
# -------------------------------------------------------
def extract_tables_from_pdf(path: str) -> List[Tuple[str, pd.DataFrame]]:
    tables: List[Tuple[str, pd.DataFrame]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                extracted = page.extract_tables() or []
                for table_idx, table in enumerate(extracted):
                    if not table or len(table) < 2:
                        continue
                    header = table[0]
                    rows = table[1:]
                    df = pd.DataFrame(rows, columns=header)
                    if not df.empty:
                        tables.append(
                            (
                                f"pdf_page_{page_idx + 1}_table_{table_idx + 1}",
                                df,
                            )
                        )
    except Exception as e:
        print("PDF table extraction error:", e)
    return tables


# -------------------------------------------------------
# Extract tables (Excel / CSV / PDF)
# -------------------------------------------------------
def extract_tables(path: str) -> List[Tuple[str, pd.DataFrame]]:
    p = path.lower()

    if p.endswith((".xlsx", ".xls")):
        xls = pd.ExcelFile(path)
        result: List[Tuple[str, pd.DataFrame]] = []
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            if not df.empty:
                result.append((sheet, df))
        return result

    if p.endswith(".csv"):
        df = pd.read_csv(path)
        if not df.empty:
            return [("csv", df)]

    if p.endswith(".pdf"):
        return extract_tables_from_pdf(path)

    return []


# -------------------------------------------------------
# Insert structured tables into Postgres
# -------------------------------------------------------
def insert_rows(file_id: str, table_name: str, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        row_data: Dict[str, Any] = {}

        for col in df.columns:
            val = row[col]

            # Pandas Timestamp → Python datetime
            if hasattr(val, "to_pydatetime"):
                val = val.to_pydatetime()

            # datetime/date → ISO string
            if isinstance(val, (_dt.datetime, _dt.date)):
                val = val.isoformat()

            # NaN → None
            if pd.isna(val):
                val = None

            row_data[str(col)] = val

        execute(
            """
            INSERT INTO extracted_rows (file_id, table_name, row_data)
            VALUES (%s, %s, %s)
            """,
            (file_id, table_name, Json(row_data)),
        )


# -------------------------------------------------------
# Extract text from file (with OCR fallback stub)
# -------------------------------------------------------
def extract_full_text(filename: str, file_bytes: bytes) -> str:
    f = filename.lower()

    # PDF
    if f.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)

        # If no text → scanned PDF → use Mistral OCR
        if not text.strip():
            print("📌 PDF text empty → using Mistral OCR")
            text = extract_text_via_ocr(file_bytes)

        return text

    # DOCX
    if f.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    # TXT
    if f.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    return ""


# -------------------------------------------------------
# Main ingest entrypoint
# -------------------------------------------------------
def ingest_file(filename: str, content_type: str, file_bytes: bytes) -> str:
    # 1. Save file
    path = save_uploaded_file(filename, file_bytes)
    file_id = str(uuid.uuid4())

    # 2. Extract full text
    full_text = extract_full_text(filename, file_bytes)

    # 3. Classify document type
    doc_type = "unknown"
    if full_text.strip():
        try:
            doc_type = classify_document(full_text[:2000])
        except Exception as e:
            print("Classification error:", e)

    # 4. Save metadata (including doc_type)
    execute(
        """
        INSERT INTO uploaded_files (id, filename, content_type, storage_path, doc_type)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (file_id, filename, content_type, path, doc_type),
    )

    # 5. Save raw text if any
    if full_text.strip():
        execute(
            """
            INSERT INTO extracted_text (file_id, text)
            VALUES (%s, %s)
            """,
            (file_id, full_text),
        )

    # 6. Extract tables (Excel, CSV, PDF)
    tables = extract_tables(path)
    for table_name, df in tables:
        insert_rows(file_id, table_name, df)

    return file_id
