# core/services/file_ingest_service.py

import os
import uuid
import pandas as pd
from typing import List, Dict, Any, Tuple
from psycopg2.extras import Json
from core.storage.postgres_client import execute

# --- FIX: Local-friendly path ---
RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "./data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)


# -------------------------------------------------------
# Save uploaded file
# -------------------------------------------------------
def save_uploaded_file(filename: str, file_bytes: bytes) -> str:
    unique_name = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(RAW_DATA_DIR, unique_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


# -------------------------------------------------------
# Extract structured tables (Excel, CSV)
# -------------------------------------------------------
def extract_tables(path: str) -> List[Tuple[str, pd.DataFrame]]:
    if path.lower().endswith((".xlsx", ".xls")):
        xls = pd.ExcelFile(path)
        tables = []
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            if not df.empty:
                tables.append((sheet, df))
        return tables

    if path.lower().endswith(".csv"):
        df = pd.read_csv(path)
        if not df.empty:
            return [("csv", df)]

    return []


# -------------------------------------------------------
# Insert extracted rows into Postgres
# -------------------------------------------------------
def insert_rows(file_id: uuid.UUID, table_name: str, df: pd.DataFrame):
    import datetime as _dt

    for _, row in df.iterrows():
        row_data: Dict[str, Any] = {}

        for col in df.columns:
            val = row[col]

            # Pandas Timestamp → Python datetime
            if hasattr(val, "to_pydatetime"):
                val = val.to_pydatetime()

            # datetime/date → string
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
            (str(file_id), table_name, Json(row_data)),
        )


# -------------------------------------------------------
# Main ingest entry
# -------------------------------------------------------
def ingest_file(filename: str, content_type: str, file_bytes: bytes) -> str:
    path = save_uploaded_file(filename, file_bytes)
    file_id = uuid.uuid4()

    execute(
        """
        INSERT INTO uploaded_files (id, filename, content_type, storage_path)
        VALUES (%s, %s, %s, %s)
        """,
        (str(file_id), filename, content_type, path),
    )

    tables = extract_tables(path)

    for table_name, df in tables:
        insert_rows(file_id, table_name, df)

    return str(file_id)
