"""
global_sanitization.py  —  MINIMAL STUB for testing.
Replace with the real RF global_sanitization.py when available.
"""
import re


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename according to RF rules:
    - lowercase everything
    - & becomes 'and'
    - spaces and dashes become _
    - every non a-z / 0-9 character becomes _
    - multiple underscores become one
    - remove underscores from start/end
    - fallback to 'file' if empty
    """
    name = name.lower()
    name = name.replace("&", "and")
    name = re.sub(r"[\s-]+", "_", name)
    name = re.sub(r"[^a-z0-9_.]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name or "file"


def sanitize_folder_name(name: str) -> str:
    """Same rules as filename, but no extension handling."""
    return sanitize_filename(name)
