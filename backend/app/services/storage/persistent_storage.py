"""Persistent recruiter-scoped resume storage service.

Saves original candidate resumes into organized private directories on disk:
  storage/resumes/{recruiter_id}/{candidate_id}.pdf
Never allows path traversal and strictly validates ownership before retrieval.
"""

import os
import shutil
import logging
from typing import Dict, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base private storage directory
BASE_STORAGE_DIR = os.path.abspath(settings.RESUME_STORAGE_DIR)
os.makedirs(BASE_STORAGE_DIR, exist_ok=True)


def _get_safe_filename(candidate_id: str, original_filename: str) -> str:
    """Generate safe internal file name with extension."""
    lower = original_filename.lower()
    ext = ".pdf" if lower.endswith(".pdf") else ".docx" if lower.endswith(".docx") else ".bin"
    safe_id = "".join(c for c in candidate_id if c.isalnum() or c in ("-", "_"))
    return f"{safe_id}{ext}"


def _get_recruiter_dir(recruiter_id: str) -> str:
    """Get or create private recruiter storage directory."""
    safe_recruiter_id = "".join(c for c in recruiter_id if c.isalnum() or c in ("-", "_"))
    recruiter_dir = os.path.abspath(os.path.join(BASE_STORAGE_DIR, safe_recruiter_id))
    # Security: Verify path is within BASE_STORAGE_DIR
    if os.path.commonpath([recruiter_dir, BASE_STORAGE_DIR]) != BASE_STORAGE_DIR:
        raise ValueError("Invalid recruiter directory path detected")
    os.makedirs(recruiter_dir, exist_ok=True)
    return recruiter_dir


def store_persistent_resume(
    recruiter_id: str,
    candidate_id: str,
    original_filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> Optional[str]:
    """Store candidate resume file into private recruiter vault.

    Returns the safe relative or absolute file path.
    """
    if not recruiter_id or not candidate_id or not content:
        return None

    try:
        recruiter_dir = _get_recruiter_dir(recruiter_id)
        filename = _get_safe_filename(candidate_id, original_filename)
        target_path = os.path.abspath(os.path.join(recruiter_dir, filename))

        # Path traversal guard
        if os.path.commonpath([target_path, recruiter_dir]) != recruiter_dir:
            logger.error(f"Path traversal blocked for candidate {candidate_id}")
            return None

        with open(target_path, "wb") as f:
            f.write(content)

        return target_path
    except Exception as exc:
        logger.error(f"Failed to persist resume file: {exc}", exc_info=True)
        return None


def get_persistent_resume(
    recruiter_id: str,
    candidate_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieve verified resume file path and metadata for an authorized recruiter."""
    if not recruiter_id or not candidate_id:
        return None

    try:
        recruiter_dir = _get_recruiter_dir(recruiter_id)
        for ext in (".pdf", ".docx", ".bin"):
            filename = f"{candidate_id}{ext}"
            target_path = os.path.abspath(os.path.join(recruiter_dir, filename))
            if os.path.exists(target_path):
                content_type = (
                    "application/pdf"
                    if ext == ".pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                return {
                    "file_path": target_path,
                    "filename": f"resume_{candidate_id}{ext}",
                    "content_type": content_type,
                    "size": os.path.getsize(target_path),
                }

        # Fallback: check session temporary vault if not yet migrated
        from app.services.storage.resume_storage import get_resume_file
        session_file = get_resume_file(candidate_id)
        if session_file and os.path.exists(session_file.get("file_path", "")):
            # Auto-promote from temp vault to recruiter persistent directory
            try:
                dest = _get_safe_filename(candidate_id, session_file.get("filename", "resume.pdf"))
                dest_path = os.path.join(recruiter_dir, dest)
                shutil.copy2(session_file["file_path"], dest_path)
                session_file["file_path"] = dest_path
                return session_file
            except Exception:
                return session_file

        return None
    except Exception as exc:
        logger.error(f"Error accessing resume file: {exc}")
        return None


def delete_persistent_resume(
    recruiter_id: str,
    candidate_id: str,
) -> bool:
    """Delete a candidate's resume file safely."""
    if not recruiter_id or not candidate_id:
        return False

    try:
        recruiter_dir = _get_recruiter_dir(recruiter_id)
        for ext in (".pdf", ".docx", ".bin"):
            filename = f"{candidate_id}{ext}"
            target_path = os.path.abspath(os.path.join(recruiter_dir, filename))
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except Exception:
                    pass

        # Also remove from session vault
        from app.services.storage.resume_storage import delete_resume_file
        delete_resume_file(candidate_id)

        return True
    except Exception as exc:
        logger.warning(f"Error deleting persistent resume for candidate {candidate_id}: {exc}")
        return False


def delete_recruiter_analysis_resumes(
    recruiter_id: str,
    candidate_ids: list,
) -> int:
    """Delete all candidate files belonging to a specific analysis."""
    deleted = 0
    for cid in candidate_ids:
        if delete_persistent_resume(recruiter_id, cid):
            deleted += 1
    return deleted
