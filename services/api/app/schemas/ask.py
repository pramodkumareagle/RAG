# app/schemas/ask.py
from typing import List, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    doc_id: str
    chunk: Optional[int]
    score: float
    text: str

class AskRequest(BaseModel):
    query: str = Field(..., description="User question")
    top_k: int = Field(5, description="Number of top documents to retrieve")

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    sources: list = []

