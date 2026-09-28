from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.search import SearchRequest
from app.services.auth_dependency import get_current_user
from app.services.similarity_service import search_similar_chunks


router = APIRouter(
    prefix="/api/search",
    tags=["Semantic Search"]
)


@router.post("/")
def semantic_search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = search_similar_chunks(
        db=db,
        query=data.query,
        user_id=current_user.id,
        top_k=data.top_k
    )

    return {
        "query": data.query,
        "results": results
    }