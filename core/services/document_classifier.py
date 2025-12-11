# core/services/document_classifier.py
import os
import requests


MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_OCR_MODEL = os.getenv("MISTRAL_OCR_MODEL", "mistral-large-latest")


def classify_document(text: str) -> str:
    """
    Ask Mistral to identify the REAL document type.
    Ensures only a clean label is returned.
    """

    if len(text) > 4000:
        text = text[:4000]

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": MISTRAL_OCR_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict document classifier.\n"
                    "Return ONLY the document type.\n"
                    "Return ONLY a SINGLE word or short phrase.\n"
                    "Do NOT say 'the document is', do NOT explain, do NOT acknowledge.\n"
                    "IF YOU UNDERSTAND, DO NOT SAY 'understood'. Just classify.\n"
                )
            },
            {
                "role": "user",
                "content": (
                    "Classify the document type from the following content.\n"
                    "Return ONLY the type. Examples: bank statement, payslip, resume, invoice, bill, contract.\n\n"
                    f"Document content:\n{text}"
                ),
            },
        ],
        "temperature": 0.1
    }

    import json
    print("🔍 classify_document payload:", json.dumps(body, indent=2))

    try:
        res = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=body
        )
        res.raise_for_status()

        raw = res.json()["choices"][0]["message"]["content"].strip()

        print("🔎 Raw LLM Output:", raw)

         
        clean = raw.split("\n")[0].strip()  # only first line  
        clean = clean.replace("Document type:", "").strip()
        clean = clean.replace("Type:", "").strip()
        clean = clean.replace("It's", "").strip()

        # If model still returns junk like "Understood"  
        bad_words = ["understood", "okay", "ok", "sure"]
        if clean.lower() in bad_words:
            clean = "unknown"

        print("🏷️ Final Classified Label:", clean)
        return clean.lower()

    except Exception as e:
        print("❌ Error in classify_document:", str(e))
        return "unknown"


