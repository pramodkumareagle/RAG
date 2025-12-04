# core/services/document_classifier.py

from transformers import pipeline

_classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
)

DOC_LABELS = [
    "invoice",
    "resume",
    "tabular pdf",
    "bank statement",
    "financial report",
    "generic text document",
    "scanned document",
]


def classify_document(text: str) -> str:
    """
    Classify text into one of the predefined DOC_LABELS.
    """
    result = _classifier(
        text,
        DOC_LABELS,
        multi_label=False,
    )
    return result["labels"][0]
