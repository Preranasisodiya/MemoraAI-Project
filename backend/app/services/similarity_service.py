import numpy as np

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding


def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a, dtype=np.float32)
    b = np.array(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def search_similar_chunks(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
):
    query_embedding = generate_embedding(query)

    chunks = (
        db.query(DocumentChunk, Document)
        .join(
            Document,
            DocumentChunk.document_id == Document.id
        )
        .filter(
            Document.user_id == user_id,
            DocumentChunk.embedding.isnot(None)
        )
        .all()
    )

    results = []

    for chunk, document in chunks:
        similarity = cosine_similarity(
            query_embedding,
            chunk.embedding
        )

        results.append({
            "chunk_id": chunk.id,
            "document_id": document.id,
            "filename": document.filename,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "similarity": similarity,
        })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return results[:top_k]