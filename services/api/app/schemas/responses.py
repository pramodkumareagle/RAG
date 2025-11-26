from pydantic import BaseModel
from typing import Any, Optional
from core.utils.json_cleaner import clean_for_json

class ResponseEnvelope(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs):
        # override dict() to ensure JSON-safe output
        raw = super().dict(*args, **kwargs)
        raw["data"] = clean_for_json(raw.get("data"))
        return raw
