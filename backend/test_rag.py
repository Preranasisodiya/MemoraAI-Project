from app.database.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.rag_service import build_context


db = SessionLocal()

try:
    result = build_context(
        db=db,
        query="What is machine learning?",
        user_id=1,
        top_k=5,
    )

    print("RAG context generation completed")
    print()
    print("Query:")
    print(result["query"])

    print()
    print("Sources:")

    for source in result["sources"]:
        print(
            f"- {source['filename']} | "
            f"Similarity: {source['similarity']:.4f}"
        )

    print()
    print("Generated Context:")
    print("=" * 70)
    print(result["context"])
    print("=" * 70)

finally:
    db.close()