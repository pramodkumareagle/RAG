# core/services/file_ingest_service.py
import datetime as _dt
from typing import List, Tuple, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session

from services.api.app.models import ExtractedRow, ExtractedText


# -------------------------------------------------------
# Normalize DataFrame values safely
# -------------------------------------------------------
def normalize_cell(val):
    """Convert Pandas/numpy datatypes into JSON-safe Python."""
    import pandas as pd
    import numpy as np

    # Convert Pandas Series → list
    if isinstance(val, pd.Series):
        return val.tolist()

    # Convert numpy arrays → list
    if isinstance(val, np.ndarray):
        return val.tolist()

    # Convert Timestamp → datetime
    if hasattr(val, "to_pydatetime"):
        val = val.to_pydatetime()

    # Convert datetime → ISO string
    if isinstance(val, (_dt.datetime, _dt.date)):
        return val.isoformat()

    # Convert NaN to None
    try:
        if pd.isna(val):
            return None
    except:
        pass

    return val


# -------------------------------------------------------
# Insert table rows into extracted_rows
# -------------------------------------------------------
def insert_rows(db: Session, file_id: str, table_name: str, df: pd.DataFrame):
    for _, row in df.iterrows():
        row_data: Dict[str, Any] = {}

        for col in df.columns:
            row_data[col] = normalize_cell(row[col])

        db.add(ExtractedRow(
            file_id=file_id,
            table_name=table_name,
            row_data=row_data
        ))


# -------------------------------------------------------
# INGEST TEXT + TABLES (after upload)
# -------------------------------------------------------
def ingest_file(
    db: Session,
    file_id: str,
    extracted_text: str,
    extracted_tables: List[Tuple[str, pd.DataFrame]]
):
    """
    Saves:
    ✔ Extracted text
    ✔ Extracted tables
    to DB using SQLAlchemy ORM.
    """

    # Save extracted text
    if extracted_text.strip():
        db.add(ExtractedText(
            file_id=file_id,
            text=extracted_text
        ))

    # Save table rows
    for table_name, df in extracted_tables:
        insert_rows(db, file_id, table_name, df)

    db.commit()
