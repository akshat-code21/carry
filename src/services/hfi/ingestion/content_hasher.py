"""Content hash utility for deduplication."""

import hashlib


def compute_hash(text: str) -> str:
    """Compute a SHA-256 hash of text for content deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
