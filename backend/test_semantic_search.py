from app.database.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.similarity_service import search_similar_chunks


db = SessionLocal()

try:
    results = search_similar_chunks(
        db=db,
        query="What is machine learning?",
        user_id=1,
        top_k=5,
    )

    print("Semantic search completed")
    print("Results found:", len(results))

    for index, result in enumerate(results, start=1):
        print()
        print("Result:", index)
        print("Filename:", result["filename"])
        print("Chunk:", result["chunk_index"])
        print("Similarity:", round(result["similarity"], 4))
        print("Content:", result["content"][:300])

finally:
    db.close()