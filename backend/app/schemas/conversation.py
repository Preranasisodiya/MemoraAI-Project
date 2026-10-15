from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel


class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str
    sources: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttachedDocumentInfo(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []
    attached_documents: List[AttachedDocumentInfo] = []

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    document_ids: Optional[List[int]] = None


class AttachDocumentRequest(BaseModel):
    document_id: int
