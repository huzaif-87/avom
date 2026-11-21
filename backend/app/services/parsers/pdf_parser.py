"""Enhanced PDF parser using PyMuPDF (fitz) with scan detection, OCR fallback, and diagnostics."""

import io
import os
import shutil
import logging
from typing import List, Optional, Tuple
import fitz  # PyMuPDF

# Check if PIL and pytesseract are available for optional OCR fallback
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False



def _find_tesseract_binary() -> Optional[str]:
    """Check if tesseract binary is accessible on PATH or common Windows locations."""
    # 1. Environment variable override
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and os.path.exists(env_cmd):
        return env_cmd

    # 2. Check PATH
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    # 3. Common Windows installation directories
    common_win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in common_win_paths:
        if os.path.exists(p):
            return p

    return None


def extract_text_from_pdf(
    file_bytes: bytes, filename: str = ""
) -> Tuple[str, List[str], Optional[str], int, str]:
    """Extract full text from a PDF file with scan detection and OCR fallback.

    Args:
        file_bytes: Binary content of the PDF file.
        filename: Optional filename for logging/diagnostics.

    Returns:
        Tuple of (extracted_text, warnings_list, error_message_or_None, page_count, extraction_status)
        extraction_status is one of: "success", "partial", "failed"
    """
    warnings: List[str] = []

    if not file_bytes:
        return "", ["PDF file is empty (0 bytes)."], "Empty file", 0, "failed"

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning(f"Failed to open/parse PDF {filename}: {exc}")
        return (
            "",
            [f"Unable to read PDF file: file may be corrupted, password-protected, or malformed ({str(exc)})"],
            "Corrupted or invalid PDF",
            0,
            "failed",
        )

    page_count = len(doc)
    page_texts: List[str] = []
    has_images_detected = False
    ocr_attempted = False
    ocr_success = False

    try:
        # Step 1: Standard text extraction per page
        for page_idx in range(page_count):
            page = doc[page_idx]
            text = page.get_text()

            # Check for embedded raster images
            image_list = page.get_images()
            if image_list:
                has_images_detected = True

            if text and text.strip():
                page_texts.append(text.strip())

        full_text = "\n\n".join(page_texts).strip()

        # Step 2: Check for suspiciously short or empty extraction
        # A multi-page resume with < 50 characters is likely scanned or image-based
        is_scanned_candidate = (
            len(full_text) < 50 and (has_images_detected or page_count > 0)
        )

        if is_scanned_candidate:
            tess_bin = _find_tesseract_binary()

            if PYTESSERACT_AVAILABLE and PIL_AVAILABLE and tess_bin:
                # Configure pytesseract binary path if needed
                pytesseract.pytesseract.tesseract_cmd = tess_bin
                ocr_attempted = True
                ocr_texts: List[str] = []

                logger.info(f"Running OCR fallback on scanned PDF {filename} ({page_count} pages)...")
                try:
                    for page_idx in range(page_count):
                        page = doc[page_idx]
                        # Render page to high-res image
                        pix = page.get_pixmap(dpi=200)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_result = pytesseract.image_to_string(img)
                        if ocr_result and ocr_result.strip():
                            ocr_texts.append(ocr_result.strip())

                    ocr_full = "\n\n".join(ocr_texts).strip()
                    if len(ocr_full) > len(full_text):
                        full_text = ocr_full
                        ocr_success = True
                        warnings.append("Text extracted via Optical Character Recognition (OCR) fallback.")
                except Exception as ocr_err:
                    logger.warning(f"OCR execution failed on {filename}: {ocr_err}")
                    warnings.append(f"OCR execution encountered an error: {str(ocr_err)}")

            if not ocr_success:
                if not PYTESSERACT_AVAILABLE or not PIL_AVAILABLE or not tess_bin:
                    warnings.append(
                        "Document appears to be scanned or image-based (contains images with minimal extractable text). "
                        "OCR is required to read image text, but the local Tesseract OCR engine was not found on the host system. "
                        "To enable scanned PDF extraction, install Tesseract OCR (e.g. https://github.com/UB-Mannheim/tesseract/wiki)."
                    )
                else:
                    warnings.append(
                        "Document appears to be scanned or image-based, but OCR was unable to extract legible text."
                    )

        # Step 3: Determine extraction status
        if not full_text:
            extraction_status = "failed"
            warnings.append("No extractable text found in PDF document.")
        elif len(full_text) < 50:
            extraction_status = "partial"
            warnings.append(f"Suspiciously short text extracted ({len(full_text)} characters for {page_count} page(s)). Parsing may be incomplete.")
        else:
            extraction_status = "success"

        return full_text, warnings, None, page_count, extraction_status
    except Exception as exc:
        logger.error(f"Error during PDF text extraction for {filename}: {exc}", exc_info=True)
        return "", [f"Error extracting text from PDF: {str(exc)}"], "Extraction failed", page_count, "failed"
    finally:
        try:
            doc.close()
        except Exception:
            pass
