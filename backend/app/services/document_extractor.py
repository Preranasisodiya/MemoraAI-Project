from pathlib import Path

import pymupdf
import pytesseract
from docx import Document as DocxDocument
from PIL import Image


# Explicit Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF.

    First attempts normal text extraction.
    If no usable text is found, falls back to OCR
    for scanned/image-based PDFs.
    """

    pdf = pymupdf.open(file_path)

    extracted_pages = []

    # First attempt: normal PDF text extraction
    for page in pdf:
        text = page.get_text("text")

        if text and text.strip():
            extracted_pages.append(text)

    extracted_text = "\n".join(extracted_pages).strip()

    # If normal extraction worked, use it
    if extracted_text:
        pdf.close()
        return extracted_text

    # Second attempt: OCR for scanned PDFs
    ocr_pages = []

    for page in pdf:
        # Render page as an image
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples,
        )

        # OCR the page image
        text = pytesseract.image_to_string(
            image,
            timeout=30,
        )

        if text and text.strip():
            ocr_pages.append(text)

    pdf.close()

    return "\n".join(ocr_pages).strip()


def extract_docx_text(file_path: str) -> str:
    """
    Extract text from a DOCX file.
    """

    document = DocxDocument(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def extract_txt_text(file_path: str) -> str:
    """
    Extract text from a TXT file.
    """

    return Path(file_path).read_text(
        encoding="utf-8",
        errors="ignore",
    )


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract text based on file type.
    """

    file_type = file_type.lower().lstrip(".")

    if file_type == "pdf":
        return extract_pdf_text(file_path)

    elif file_type == "docx":
        return extract_docx_text(file_path)

    elif file_type == "txt":
        return extract_txt_text(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {file_type}"
        )