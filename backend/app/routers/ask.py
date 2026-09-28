from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
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
    rag_data = build_context(
        db=db,
        query=data.query,
        user_id=current_user.id,
        top_k=data.top_k
    )

    answer = generate_answer(
        query=data.query,
        context=rag_data["context"]
    )

    return {
        "query": data.query,
        "answer": answer,
        "sources": rag_data["sources"]
    }