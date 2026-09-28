import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.auth_dependency import get_current_user
from app.services.document_processor import process_document


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.post("/", response_model=DocumentResponse)
def create_document(
    data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_document = Document(
        user_id=current_user.id,
        title=data.title,
        filename=data.filename,
        file_type=data.file_type,
        file_path=data.file_path,
        file_hash=""
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt"
    }

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    original_filename = file.filename
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are allowed"
        )

    file_contents = file.file.read()

    if not file_contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    file_hash = hashlib.sha256(file_contents).hexdigest()

    upload_directory = Path(
        f"uploads/{current_user.id}"
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    stored_filename = (
        f"{file_hash}{file_extension}"
    )

    file_path = upload_directory / stored_filename

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_contents)

        result = process_document(
            db=db,
            file_path=file_path,
            user_id=current_user.id
        )

        if result["status"] == "duplicate":
            if file_path.exists():
                file_path.unlink()

            raise HTTPException(
                status_code=409,
                detail="This file has already been uploaded"
            )

        if result["status"] == "no_text":
            if file_path.exists():
                file_path.unlink()

            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the document"
            )

        return {
            "message": "Document uploaded and processed successfully",
            "document_id": result["document_id"],
            "user_id": current_user.id,
            "filename": result["filename"],
            "file_type": file_extension.replace(".", ""),
            "file_path": str(file_path),
            "file_hash": file_hash,
            "chunks_created": result["chunks_created"]
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(exc)}"
        )