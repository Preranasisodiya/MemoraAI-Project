from pathlib import Path

from app.database.database import SessionLocal
from app.models.user import User
from app.services.document_processor import process_document


TEST_FILE = Path(
    r"D:\MemoraAI_Knowledge\Sem_5\Image_and_Video_Processing\Image_and_Video_Processing__Sem-V__Batch_2024-25__Re_Exam_b2DgztjxZT.pdf"
)


db = SessionLocal()

try:
    result = process_document(
        db=db,
        file_path=TEST_FILE,
        user_id=2,
    )

    print("\n=== Document Processor Test ===")
    print(result)
    print("\n=== Test Complete ===")

finally:
    db.close()