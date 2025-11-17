from pydantic import BaseModel
from typing import List, Optional


class AskRequest(BaseModel):
    query: str
    top_k: int = 5


class Hit(BaseModel):
    score: float
    text: str
    filename: Optional[str]
    source_path: Optional[str]
    chunk: int
    doc_id: Optional[str]


class AskResponse(BaseModel):
    answer: str
    results: List[Hit]

