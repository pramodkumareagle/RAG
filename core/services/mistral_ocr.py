import os
import base64
from mistralai import Mistral

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL   = os.getenv("MISTRAL_OCR_MODEL", "mistral-large-latest")  # supports vision

client = Mistral(api_key=MISTRAL_API_KEY)


def extract_text_via_mistral_ocr(pdf_bytes: bytes) -> str:
    """
    Uses Mistral multimodal OCR to read scanned PDFs.
    Converts PDF → base64 and sends as an image attachment.
    """

    # Encode PDF into base64 for Mistral
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    prompt = "Extract all text from this scanned document. Preserve layout if possible."

    try:
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "document",
                            "document": {
                                "format": "pdf",
                                "b64": b64
                            }
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message["content"]

    except Exception as e:
        print("Mistral OCR error:", e)
        return ""

