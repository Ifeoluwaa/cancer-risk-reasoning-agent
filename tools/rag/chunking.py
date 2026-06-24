"""chunking.py

Text chunking utilities for dividing documents into smaller, coherent text segments.
"""

from typing import List


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """Splits a body of text into smaller overlapping chunks by character length.

    Args:
        text: The raw input document text.
        chunk_size: Maximum character count per chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of string chunks.
    """
    if not text:
        return []

    # Sanity checks
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be strictly less than chunk_size.")

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= text_len:
            break
            
        start += (chunk_size - chunk_overlap)

    return chunks
