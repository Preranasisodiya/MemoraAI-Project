from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, ChatMessage
from app.schemas.ask import AskRequest
from app.services.auth_dependency import get_current_user
from app.services.rag_service import build_context
from app.services.llm_service import generate_answer


router = APIRouter(prefix="/api/ask", tags=["RAG Q&A"])


@router.post("/")
def ask_question(
    data: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Resolve or create conversation
    from app.models.document import Document

    conversation = None
    if data.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == data.conversation_id,
                Conversation.user_id == current_user.id
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        # If user explicitly passed document_ids to attach to this ongoing conversation
        if data.document_ids:
            for doc_id in data.document_ids:
                doc = (
                    db.query(Document)
                    .filter(Document.id == doc_id, Document.user_id == current_user.id)
                    .first()
                )
                if doc and doc not in conversation.attached_documents:
                    conversation.attached_documents.append(doc)
            db.commit()
            db.refresh(conversation)
    else:
        # Create a new conversation title from the first query
        clean_title = data.query.strip().split("\n")[0][:45]
        if len(data.query.strip()) > 45:
            clean_title += "..."
        conversation = Conversation(
            user_id=current_user.id,
            title=clean_title or "New Conversation"
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

    # 2. Retrieve recent conversation history for context
    past_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    formatted_history = [
        {"sender": m.sender, "content": m.content}
        for m in past_messages[-6:]
    ]

    # Determine document filter: if conversation has attached documents, prioritize those
    attached_doc_ids = [d.id for d in conversation.attached_documents]
    filter_doc_ids = attached_doc_ids if attached_doc_ids else None

    # 3. Retrieve relevant document chunks
    rag_data = build_context(
        db=db,
        query=data.query,
        user_id=current_user.id,
        top_k=data.top_k,
        document_ids=filter_doc_ids
    )

    # 4. Generate answer using configured LLM (Groq / Ollama)
    answer = generate_answer(
        query=data.query,
        context=rag_data["context"],
        chat_history=formatted_history
    )

    # 5. Persist user question and assistant answer
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        sender="user",
        content=data.query,
        created_at=datetime.utcnow()
    )
    db.add(user_msg)

    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        sender="assistant",
        content=answer,
        sources=rag_data["sources"],
        created_at=datetime.utcnow()
    )
    db.add(assistant_msg)

    conversation.updated_at = datetime.utcnow()
    db.commit()

    return {
        "query": data.query,
        "answer": answer,
        "conversation_id": conversation.id,
        "sources": rag_data["sources"]
    }