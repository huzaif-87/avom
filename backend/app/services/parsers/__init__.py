"""Document parser modules (PDF and DOCX)."""

from app.services.parsers.pdf_parser import extract_text_from_pdf
from app.services.parsers.docx_parser import extract_text_from_docx

__all__ = ["extract_text_from_pdf", "extract_text_from_docx"]
