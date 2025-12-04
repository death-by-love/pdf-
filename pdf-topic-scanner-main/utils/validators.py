"""Validation utilities for inputs and file types."""
from typing import Tuple


def is_pdf_filename(path: str) -> bool:
    return str(path).lower().endswith(".pdf")


def validate_uploaded_file(file) -> Tuple[bool, str]:
    """Validate an uploaded file-like object.

    Returns (is_valid, message)
    """
    if file is None:
        return False, "No file provided"
    name = getattr(file, "name", None)
    if not name:
        return False, "Uploaded object has no filename"
    if not is_pdf_filename(name):
        return False, "File is not a PDF"
    return True, "OK"
