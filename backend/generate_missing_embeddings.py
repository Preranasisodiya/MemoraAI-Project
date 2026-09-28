from app.database.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import generate_embedding

db = SessionLocal()

try:
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.embedding.is_(None))
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        .all()
    )

    print(f"Found {len(chunks)} chunks without embeddings.\n")

    updated = 0

    for chunk in chunks:
        embedding = generate_embedding(chunk.content)
        chunk.embedding = embedding
        updated += 1

        print(
            f"Document {chunk.document_id} | "
            f"Chunk {chunk.chunk_index} | "
            f"Embedding Generated"
        )

    db.commit()

    print("\n===================================")
    print("Embedding generation completed.")
    print(f"Total embeddings generated: {updated}")
    print("===================================")

finally:
    db.close()