from app.database.database import SessionLocal
from app.models.user import User
from app.services.folder_processor import process_folder


TEST_FOLDER = r"D:\MemoraAI_Knowledge"


db = SessionLocal()

try:
    result = process_folder(
        db=db,
        folder_path=TEST_FOLDER,
        user_id=2,
    )

    print("\n=== MemoraAI Folder Processor Test ===")

    print("\nRoot folder:")
    print(result["root_folder"])

    print("\nStatistics:")

    for key, value in result["statistics"].items():
        print(f"  {key}: {value}")

    print("\nProcessed:")

    for item in result["processed"]:
        print(
            f"  ✓ {item['filename']} "
            f"(chunks: {item['chunks_created']})"
        )

    print("\nDuplicates:")

    for item in result["duplicates"]:
        print(
            f"  ↻ {item['filename']} "
            f"(document_id: {item['document_id']})"
        )

    print("\nErrors:")

    for error in result["errors"]:
        print(f"  ! {error['filename']}")
        print(f"    {error['error']}")

    print("\n=== Folder Processing Complete ===")

finally:
    db.close()