from pathlib import Path

from sqlalchemy.orm import Session

from app.services.folder_scanner import scan_folder
from app.services.document_processor import process_document


def process_folder(
    db: Session,
    folder_path: str,
    user_id: int,
):
    """
    Scan a selected folder recursively and process
    every supported document.
    """

    # 1. Scan the selected folder
    scan_result = scan_folder(folder_path)

    processed = []
    duplicates = []
    errors = []

    # 2. Process every supported file
    for file_path in scan_result["supported_files"]:

        try:
            result = process_document(
                db=db,
                file_path=Path(file_path),
                user_id=user_id,
            )

            if result["status"] == "processed":
                processed.append(result)

            elif result["status"] == "duplicate":
                duplicates.append(result)

        except Exception as exc:
            # Reset the database session after a failed transaction
            db.rollback()

            errors.append({
                "filename": Path(file_path).name,
                "path": str(file_path),
                "error": str(exc),
            })

    # 3. Return processing summary
    return {
        "root_folder": scan_result["root_folder"],

        "statistics": {
            "total_files_found":
                scan_result["statistics"]["total_files_found"],

            "supported_files":
                scan_result["statistics"]["supported"],

            "skipped_files":
                scan_result["statistics"]["skipped"],

            "processed":
                len(processed),

            "duplicates":
                len(duplicates),

            "errors":
                len(errors),
        },

        "processed": processed,
        "duplicates": duplicates,
        "errors": errors,
        "skipped_files": scan_result["skipped_files"],
    }