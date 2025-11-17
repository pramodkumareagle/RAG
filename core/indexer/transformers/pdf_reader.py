from pypdf import PdfReader

def read_pdf_file(path: str) -> str:
    reader = PdfReader(path)
    pages = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        pages.append(txt)

    return "\n".join(pages)

