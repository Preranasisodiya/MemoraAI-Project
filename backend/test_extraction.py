from app.services.document_extractor import extract_text


file_path = r"D:\MemoraAI_Knowledge\Sem_5\Image_and_Video_Processing\Image_and_Video_Processing__Sem-V__Batch_2024-25__Re_Exam_b2DgztjxZT.pdf"

text = extract_text(
    file_path,
    "pdf"
)

print("========== EXTRACTED TEXT ==========")

print(text)

print("====================================")