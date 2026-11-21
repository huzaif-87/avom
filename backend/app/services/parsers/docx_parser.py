"""Enhanced DOCX parser using python-docx with paragraph and table extraction."""

import io
import logging
from typing import List, Optional, Tuple
import docx

logger = logging.getLogger(__name__)


def extract_text_from_docx(
    file_bytes: bytes, filename: str = ""
) -> Tuple[str, List[str], Optional[str], int, str]:
    """Extract full text from a DOCX document including paragraphs and tables.

    Args:
        file_bytes: Binary content of the DOCX file.
        filename: Optional filename for logging/diagnostics.

    Returns:
        Tuple of (extracted_text, warnings_list, error_message_or_None, estimated_pages, extraction_status)
    """
    warnings: List[str] = []

    if not file_bytes:
        return "", ["DOCX file is empty (0 bytes)."], "Empty file", 0, "failed"

    try:
        stream = io.BytesIO(file_bytes)
        doc = docx.Document(stream)
    except Exception as exc:
        logger.warning(f"Failed to open/parse DOCX {filename}: {exc}")
        return (
            "",
            [f"Unable to read DOCX file: file may be corrupted, password-protected, or not a valid Word document ({str(exc)})"],
            "Corrupted or invalid DOCX",
            0,
            "failed",
        )

    try:
        text_parts: List[str] = []

        # 1. Paragraphs
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                text_parts.append(text)

        # 2. Tables
        for table in doc.tables:
            for row in table.rows:
                # Deduplicate merged cells within the row
                row_cells: List[str] = []
                seen_texts = set()
                for cell in row.cells:
                    c_text = cell.text.strip()
                    if c_text and c_text not in seen_texts:
                        seen_texts.add(c_text)
                        row_cells.append(c_text)
                if row_cells:
                    text_parts.append(" | ".join(row_cells))

        full_text = "\n".join(text_parts).strip()

        # Word docs do not store explicit page counts in plain xml without rendering engine,
        # so estimate page count based on word/character count (approx 3000 chars per standard page)
        estimated_pages = max(1, (len(full_text) // 2500) + 1) if full_text else 0

        if not full_text:
            extraction_status = "failed"
            warnings.append("No extractable text found in DOCX document.")
        elif len(full_text) < 50:
            extraction_status = "partial"
            warnings.append(f"Suspiciously short text extracted ({len(full_text)} characters). Parsing may be incomplete.")
        else:
            extraction_status = "success"

        return full_text, warnings, None, estimated_pages, extraction_status
    except Exception as exc:
        logger.error(f"Error during DOCX text extraction for {filename}: {exc}", exc_info=True)
        return "", [f"Error extracting text from DOCX: {str(exc)}"], "Extraction failed", 0, "failed"
