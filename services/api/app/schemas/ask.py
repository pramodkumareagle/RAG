# app/schemas/ask.py
from typing import List, Optional
from pydantic import BaseModel

class Citation(BaseModel):
    doc_id: str
    chunk: Optional[int]
    score: float
    text: str

class AskRequest(BaseModel):
    query: str
    top_k: int = 6

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
