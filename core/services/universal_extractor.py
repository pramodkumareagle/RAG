import io
import imghdr
import mimetypes
from PIL import Image
import pdfplumber
import pandas as pd

from core.services.text_extractor import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_via_ocr,
)
from core.services.document_classifier import classify_document


# ----------------------------------------------------
# Safe MIME Type Detection (no libmagic)
# ----------------------------------------------------
def detect_mime(filename: str, file_bytes: bytes) -> str:
    """
    Detect MIME using:
    1. File extension → mimetypes
    2. Image detector → imghdr
    """
    # Try extension-based detection first
    mime, _ = mimetypes.guess_type(filename)
    if mime:
        return mime

    # Try image detection
    img_type = imghdr.what(None, h=file_bytes)
    if img_type:
        return f"image/{img_type}"

    # Fallback
    return "application/octet-stream"


# ----------------------------------------------------
# PDF Table Extraction
# ----------------------------------------------------
def extract_pdf_tables(file_bytes: bytes):
    tables = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                extracted = page.extract_tables() or []

                for table_index, table_data in enumerate(extracted):
                    if len(table_data) < 2:
                        continue

                    header = table_data[0]
                    rows = table_data[1:]
                    df = pd.DataFrame(rows, columns=header)

                    tables.append(
                        (f"pdf_page_{page_index+1}_table_{table_index+1}", df)
                    )

    except Exception as e:
        print("Error extracting PDF tables:", e)

    return tables


# ----------------------------------------------------
# CSV + Excel (XLS/XLSX) Table Extraction
# ----------------------------------------------------
def extract_excel_csv(filename: str, file_bytes: bytes):
    name = filename.lower()
    tables = []

    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
            tables.append(("csv", df))

        elif name.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(io.BytesIO(file_bytes))
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                tables.append((sheet, df))

    except Exception as e:
        print("Excel/CSV extraction error:", e)

    return tables


# ----------------------------------------------------
# UNIVERSAL DOCUMENT EXTRACTOR
# ----------------------------------------------------
def extract_anything(filename: str, content_type: str, file_bytes: bytes):
    """
    Extracts:
    ✔ Text
    ✔ Tables
    ✔ Auto doc_type classification
    ✔ Works for ALL formats
    """

    ext = filename.lower()
    real_mime = detect_mime(filename, file_bytes)

    full_text = ""
    tables = []

    # --------------------------------------------
    # PDF
    # --------------------------------------------
    if ext.endswith(".pdf"):
        # Text-based PDF
        full_text = extract_text_from_pdf(file_bytes)

        # Scanned → use OCR
        if not full_text.strip():
            full_text = extract_text_via_ocr(file_bytes)

        # Try extracting tables
        tables = extract_pdf_tables(file_bytes)

    # --------------------------------------------
    # DOCX
    # --------------------------------------------
    elif ext.endswith(".docx"):
        full_text = extract_text_from_docx(file_bytes)

    # --------------------------------------------
    # TXT
    # --------------------------------------------
    elif ext.endswith(".txt"):
        full_text = file_bytes.decode("utf-8", errors="ignore")

    # --------------------------------------------
    # CSV / Excel
    # --------------------------------------------
    elif ext.endswith((".csv", ".xlsx", ".xls")):
        tables = extract_excel_csv(filename, file_bytes)

        # Optional: text preview from tables
        try:
            full_text = "\n\n".join(df.to_string() for _, df in tables)
        except:
            full_text = ""

    # --------------------------------------------
    # Images → OCR
    # --------------------------------------------
    elif real_mime.startswith("image/"):
        full_text = extract_text_via_ocr(file_bytes)

    # --------------------------------------------
    # Unknown formats → Try OCR fallback
    # --------------------------------------------
    else:
        full_text = extract_text_via_ocr(file_bytes)

    # --------------------------------------------
    # Auto document classification
    # --------------------------------------------
    doc_type = classify_document(full_text[:1500]) if full_text.strip() else "unknown"

    # --------------------------------------------
    # Return everything
    # --------------------------------------------
    return {
        "text": full_text or "",
        "tables": tables,
        "doc_type": doc_type,
        "detected_type": real_mime,
    }
