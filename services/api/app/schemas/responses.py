from pydantic import BaseModel
from typing import Any, Optional


class ResponseEnvelope(BaseModel):
    success: bool
    data: Any | None = None
    error: Optional[str] = None

