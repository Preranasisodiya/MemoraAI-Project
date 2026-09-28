import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_extractor import extract_text
from app.services.text_chunker import chunk_text
from app.services.embedding_service import generate_embedding


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()


def process_document(
    db: Session,
    file_path: Path,
    user_id: int,
):
    """
    Process a single document and store it in the database.

    Pipeline:
        Hash → Duplicate Check → Extract → Chunk → Embed → Store
    """

    file_path = file_path.resolve()

    # Determine file type
    file_type = file_path.suffix.lower().lstrip(".")

    # Calculate SHA-256
    file_hash = calculate_file_hash(file_path)

    # Check whether this file already exists for this user
    existing_document = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.file_hash == file_hash,
        )
        .first()
    )

    # Handle existing document
    if existing_document:

        existing_chunk_count = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == existing_document.id
            )
            .count()
        )

        has_extracted_text = bool(
            existing_document.extracted_text
            and existing_document.extracted_text.strip()
        )

        # Fully processed document → genuine duplicate
        if has_extracted_text and existing_chunk_count > 0:
            return {
                "status": "duplicate",
                "document_id": existing_document.id,
                "filename": existing_document.filename,
            }

        # Incomplete old document → rebuild it
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == existing_document.id
        ).delete()

        document = existing_document

    else:
        # No existing record → create a new document
        document = Document(
            user_id=user_id,
            title=file_path.stem,
            filename=file_path.name,
            file_type=file_type,
            file_path=str(file_path),
            file_hash=file_hash,
        )

        db.add(document)
        db.flush()

    # Extract text
    extracted_text = extract_text(
        str(file_path),
        file_type,
    )

    # PostgreSQL TEXT fields cannot contain NUL (0x00) bytes.
    extracted_text = extracted_text.replace("\x00", "")

    # Reject documents for which no text could be extracted
    if not extracted_text.strip():
        db.rollback()

        return {
            "status": "no_text",
            "document_id": document.id,
            "filename": document.filename,
            "message": "No text could be extracted from the document.",
        }

    # Create chunks
    chunks = chunk_text(extracted_text)

    # Update document information
    document.title = file_path.stem
    document.filename = file_path.name
    document.file_type = file_type
    document.file_path = str(file_path)
    document.file_hash = file_hash
    document.extracted_text = extracted_text

    # Generate embeddings and store chunks
    for index, content in enumerate(chunks):

        embedding = generate_embedding(content)

        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )

        db.add(document_chunk)

    db.commit()
    db.refresh(document)

    return {
        "status": "processed",
        "document_id": document.id,
        "filename": document.filename,
        "chunks_created": len(chunks),
    }