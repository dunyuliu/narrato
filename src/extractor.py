"""Extract text from documents (.docx, .pdf)."""

from pathlib import Path

from docx import Document


def extract_text(file_path: str) -> str:
    """
    Extract all text from a document file (.docx or .pdf).

    Args:
        file_path: Path to the document file

    Returns:
        Extracted text as a single string

    Raises:
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".docx":
        return _extract_from_docx(str(file_path))
    elif extension == ".pdf":
        return _extract_from_pdf(str(file_path))
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            f"Supported formats: .docx, .pdf"
        )


def _extract_from_docx(docx_path: str) -> str:
    """
    Extract all text from a .docx file.

    Paragraphs are joined with double newlines to preserve natural reading pauses.
    Empty paragraphs are skipped.

    Args:
        docx_path: Path to the .docx file

    Returns:
        Extracted text as a single string
    """
    doc = Document(docx_path)
    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # Join paragraphs with double newlines for natural reading pauses
    return "\n\n".join(paragraphs)


def _extract_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a .pdf file.

    Uses PyPDF2 to extract text from all pages.
    Paragraphs are joined with double newlines.

    Args:
        pdf_path: Path to the .pdf file

    Returns:
        Extracted text as a single string
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError(
            "PDF support requires PyPDF2. "
            "Install with: pip install PyPDF2"
        )

    reader = PdfReader(pdf_path)
    text_lines = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text.strip():
            text_lines.append(text.strip())

    # Join pages with double newlines for natural pauses
    return "\n\n".join(text_lines)
