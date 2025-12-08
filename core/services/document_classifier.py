# core/services/document_classifier.py
import os
import requests


MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_OCR_MODEL = os.getenv("MISTRAL_OCR_MODEL", "mistral-large-latest")


def classify_document(text: str) -> str:
    """
    Classify document type using Mistral LLM.
    Returns a string label like 'invoice', 'receipt', 'contract', etc.
    """

    if len(text) > 4000:
        text = text[:4000]  # truncate to fit token limits

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": MISTRAL_OCR_MODEL,
        "messages": [
            {"role": "system", "content": "Return only one label."},
            {
                "role": "user",
                "content": (
                    "Classify the type of this document strictly into one of the following categories: \n"
                    "resume, payslip, magzinee, invoice, receipt, contract, report, letter, bill, book, memo, other.\n\n"
                    "Document content:\n" + text
                ),
            },
        ],
        "temperature": 0.0
    }

    try:
        res = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=body
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip().lower()
    except Exception as e:
        return "unknown"