from pydantic import BaseModel

class CodeChatRequest(BaseModel):
    question: str
