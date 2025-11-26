import os
import uuid
import pandas as pd
from typing import List, Dict, Any, Tuple
from psycopg2.extras import Json
from core.storage.postgres_client import execute

RAW_DATA_DIR = os.getenv("RAW_DATA_DIR", "/workspace/data/raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def save_uploaded_file(filename: str, file_bytes: bytes) -> str:
    unique = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(RAW_DATA_DIR, unique)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path

def extract_tables(path: str) -> List[Tuple[str, pd.DataFrame]]:
    if path.lower().endswith((".xlsx", ".xls")):
        xls = pd.ExcelFile(path)
        return [(sheet, xls.parse(sheet)) for sheet in xls.sheet_names]
    if path.lower().endswith(".csv"):
        return [("csv", pd.read_csv(path))]
    return []

def insert_rows(file_id: uuid.UUID, table_name: str, df: pd.DataFrame):
    for _, row in df.iterrows():
        row_data = {}
        for col in df.columns:
            val = row[col]

            # Convert timestamp types
            if hasattr(val, "to_pydatetime"):
                val = val.to_pydatetime()

            if pd.isna(val):
                val = None

            row_data[col] = val

        execute(
            """
            INSERT INTO extracted_rows (file_id, table_name, row_data)
            VALUES (%s, %s, %s)
            """,
            (str(file_id), table_name, Json(row_data))
        )

def ingest_file(filename: str, content_type: str, file_bytes: bytes):
    path = save_uploaded_file(filename, file_bytes)
    file_id = uuid.uuid4()

    execute("""
        INSERT INTO uploaded_files(id, filename, content_type, storage_path)
        VALUES (%s, %s, %s, %s)
    """, (str(file_id), filename, content_type, path))

    for table_name, df in extract_tables(path):
        insert_rows(file_id, table_name, df)

    return str(file_id)
