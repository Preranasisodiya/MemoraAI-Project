from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.document import Document
from app.schemas.conversation import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreate,
    AttachDocumentRequest,
)
from app.services.auth_dependency import get_current_user


router = APIRouter(
    prefix="/api/conversations",
    tags=["Conversations"]
)


@router.get("/", response_model=List[ConversationResponse])
def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all conversations belonging to the current user."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post("/", response_model=ConversationDetailResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation, optionally associating documents."""
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title or "New Conversation"
    )

    if data.document_ids:
        docs = (
            db.query(Document)
            .filter(
                Document.id.in_(data.document_ids),
                Document.user_id == current_user.id
            )
            .all()
        )
        conversation.attached_documents.extend(docs)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.post("/{conversation_id}/documents", response_model=ConversationDetailResponse)
def attach_document_to_conversation(
    conversation_id: int,
    data: AttachDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Attach an owned document to an owned conversation."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    document = (
        db.query(Document)
        .filter(
            Document.id == data.document_id,
            Document.user_id == current_user.id
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document not in conversation.attached_documents:
        conversation.attached_documents.append(document)
        db.commit()
        db.refresh(conversation)

    return conversation


@router.delete("/{conversation_id}/documents/{document_id}", response_model=ConversationDetailResponse)
def detach_document_from_conversation(
    conversation_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detach a document from a conversation without deleting the document from My Documents."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document in conversation.attached_documents:
        conversation.attached_documents.remove(document)
        db.commit()
        db.refresh(conversation)

    return conversation


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve details and messages of a single conversation owned by the current user."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and its messages."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()
    return None
