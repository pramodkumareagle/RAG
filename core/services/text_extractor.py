import pdfplumber
import docx
import tempfile
from core.services.mistral_ocr import extract_text_via_mistral_ocr


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Try normal PDF text extraction first (pdfplumber).
    If empty → return "" and let Mistral OCR handle it.
    """
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages)
    except:
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    d = docx.Document(tmp_path)
    return "\n".join([p.text for p in d.paragraphs])


def extract_text_via_ocr(pdf_bytes: bytes) -> str:
    """
    OCR now uses Mistral (not Tesseract).
    """
    return extract_text_via_mistral_ocr(pdf_bytes)
