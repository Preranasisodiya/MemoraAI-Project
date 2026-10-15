import hashlib
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
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

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.get("/")
def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all documents owned by the authenticated user."""
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "file_type": doc.file_type,
            "created_at": doc.created_at,
        }
        for doc in documents
    ]



@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document and all associated chunks owned by the current user."""
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Clean up file on disk if present
    try:
        p = Path(document.file_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    db.delete(document)
    db.commit()
    return None


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


def _save_and_process_file(file: UploadFile, current_user: User, db: Session) -> dict:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    original_filename = file.filename
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF, DOCX, and TXT files are allowed (received '{original_filename}')"
        )

    file_contents = file.file.read()

    if not file_contents:
        raise HTTPException(
            status_code=400,
            detail=f"File '{original_filename}' is empty"
        )

    file_hash = hashlib.sha256(file_contents).hexdigest()

    upload_directory = Path(f"uploads/{current_user.id}")
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{file_hash}{file_extension}"
    file_path = upload_directory / stored_filename

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_contents)

        result = process_document(
            db=db,
            file_path=file_path,
            user_id=current_user.id,
            original_filename=original_filename,
            original_path=str(file_path),
        )


        if result["status"] == "duplicate":
            if file_path.exists():
                file_path.unlink()
            return {
                "status": "duplicate",
                "filename": original_filename,
                "message": f"'{original_filename}' has already been uploaded."
            }

        if result["status"] == "no_text":
            if file_path.exists():
                file_path.unlink()
            return {
                "status": "no_text",
                "filename": original_filename,
                "message": f"No readable text found in '{original_filename}'."
            }

        return {
            "status": "success",
            "document_id": result["document_id"],
            "filename": original_filename,
            "message": "Processed successfully"
        }

    except Exception as exc:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process '{original_filename}': {str(exc)}"
        )


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = _save_and_process_file(file, current_user, db)
    if res["status"] == "duplicate":
        raise HTTPException(status_code=409, detail=res["message"])
    if res["status"] == "no_text":
        raise HTTPException(status_code=400, detail=res["message"])

    return {
        "message": "Documents uploaded and processed successfully.",
        "filename": res["filename"],
        "document_id": res["document_id"]
    }


@router.post("/upload-multiple")
def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process multiple uploaded files (including files extracted from nested folders).
    Returns clean status without exposing internal chunks.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    results = []
    errors = []
    processed_count = 0
    duplicate_count = 0

    for file in files:
        # Check extension before reading
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            # Skip unsupported files inside folders safely
            continue

        try:
            res = _save_and_process_file(file, current_user, db)
            if res["status"] == "success":
                processed_count += 1
                results.append({"filename": res["filename"], "status": "processed"})
            elif res["status"] == "duplicate":
                duplicate_count += 1
                results.append({"filename": res["filename"], "status": "duplicate"})
            elif res["status"] == "no_text":
                errors.append(res["message"])
        except HTTPException as he:
            errors.append(he.detail)
        except Exception as e:
            errors.append(f"Failed to process '{file.filename}': {str(e)}")

    if processed_count == 0 and duplicate_count == 0 and errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    message = "Documents uploaded and processed successfully."
    if processed_count == 0 and duplicate_count > 0:
        message = "Selected documents have already been uploaded."

    return {
        "message": message,
        "processed_count": processed_count,
        "duplicate_count": duplicate_count,
        "errors": errors
    }