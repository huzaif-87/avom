"""Temporary resume file storage service for secure in-session viewing."""

import os
import tempfile
import time
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Dedicated private session vault inside OS temp directory
VAULT_DIR = os.path.abspath(os.path.join(tempfile.gettempdir(), "talentrank_session_vault"))
os.makedirs(VAULT_DIR, exist_ok=True)

# In-memory registry: candidate_id -> file metadata
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _get_safe_stored_filename(candidate_id: str, original_filename: str) -> str:
    """Generate safe internal filename using candidate ID and validated extension."""
    lower = original_filename.lower()
    ext = ".pdf" if lower.endswith(".pdf") else ".docx" if lower.endswith(".docx") else ".bin"
    # Never allow user-supplied characters in internal filename
    safe_id = "".join(c for c in candidate_id if c.isalnum() or c in ("-", "_"))
    return f"{safe_id}{ext}"


def store_resume_file(
    candidate_id: str,
    original_filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> bool:
    """Securely store an uploaded resume file in the temporary session vault.

    Args:
        candidate_id: Unique candidate identifier.
        original_filename: User's original upload filename.
        content: Binary content of the resume.
        content_type: MIME type of the file.

    Returns:
        True if successfully saved, False otherwise.
    """
    if not candidate_id or not content:
        return False

    safe_name = _get_safe_stored_filename(candidate_id, original_filename)
    target_path = os.path.abspath(os.path.join(VAULT_DIR, safe_name))

    # Path traversal verification
    if os.path.commonpath([target_path, VAULT_DIR]) != VAULT_DIR:
        logger.error(f"Potential path traversal attempt detected for candidate {candidate_id}")
        return False

    try:
        with open(target_path, "wb") as f:
            f.write(content)

        _REGISTRY[candidate_id] = {
            "file_path": target_path,
            "filename": os.path.basename(original_filename),
            "content_type": content_type,
            "size": len(content),
            "created_at": time.time(),
        }
        return True
    except Exception as exc:
        logger.error(f"Failed to store resume for candidate {candidate_id}: {exc}", exc_info=True)
        return False


def get_resume_file(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata and verified file path for a candidate resume.

    Args:
        candidate_id: Candidate identifier.

    Returns:
        Dict with file metadata or None if not found or invalid.
    """
    info = _REGISTRY.get(candidate_id)
    if not info:
        # Check if file exists on disk with standard extension
        for ext in (".pdf", ".docx", ".bin"):
            safe_name = f"{candidate_id}{ext}"
            target_path = os.path.abspath(os.path.join(VAULT_DIR, safe_name))
            if os.path.exists(target_path):
                content_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                return {
                    "file_path": target_path,
                    "filename": f"resume_{candidate_id}{ext}",
                    "content_type": content_type,
                    "size": os.path.getsize(target_path),
                    "created_at": os.path.getctime(target_path),
                }
        return None

    file_path = info.get("file_path")
    if file_path and os.path.exists(file_path):
        return info

    return None


def delete_resume_file(candidate_id: str) -> bool:
    """Delete a candidate's stored resume from the session vault.

    Args:
        candidate_id: Candidate identifier.

    Returns:
        True if deleted or already absent, False on error.
    """
    info = _REGISTRY.pop(candidate_id, None)
    if info and info.get("file_path"):
        path = info["file_path"]
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as exc:
            logger.warning(f"Failed to delete resume file {path}: {exc}")

    # Also clean any matching files on disk
    for ext in (".pdf", ".docx", ".bin"):
        safe_name = f"{candidate_id}{ext}"
        target_path = os.path.abspath(os.path.join(VAULT_DIR, safe_name))
        try:
            if os.path.exists(target_path):
                os.remove(target_path)
        except Exception:
            pass

    return True


def clear_all_resumes() -> int:
    """Clear all stored resume files in the session vault.

    Returns:
        Count of deleted files.
    """
    count = 0
    _REGISTRY.clear()

    try:
        if os.path.exists(VAULT_DIR):
            for name in os.listdir(VAULT_DIR):
                full_path = os.path.join(VAULT_DIR, name)
                if os.path.isfile(full_path):
                    try:
                        os.remove(full_path)
                        count += 1
                    except Exception:
                        pass
    except Exception as exc:
        logger.error(f"Error clearing vault: {exc}")

    return count
