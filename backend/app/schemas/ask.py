from typing import Optional, List
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    conversation_id: Optional[int] = None
    document_ids: Optional[List[int]] = None
    top_k: int = Field(default=5, ge=1, le=20)