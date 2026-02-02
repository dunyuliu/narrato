"""Chunk text intelligently for TTS API."""

import re
from typing import List


def chunk_text(text: str, max_chunk_size: int = 4096) -> List[str]:
    """
    Split text into chunks that respect sentence boundaries.

    Uses greedy bin-packing: accumulates sentences into chunks until the next
    sentence would exceed max_chunk_size. If a single sentence exceeds
    max_chunk_size, it's split at word boundaries.

    Args:
        text: The text to chunk
        max_chunk_size: Maximum bytes per chunk (default 4096 for OpenAI TTS)

    Returns:
        List of text chunks, in order
    """
    # Split on sentence boundaries, keeping delimiters
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding this sentence would exceed the limit
        if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            # Save current chunk and start a new one
            chunks.append(current_chunk)
            current_chunk = ""

        # If this sentence alone exceeds max_chunk_size, split at word boundaries
        if len(sentence) > max_chunk_size:
            # First, add any existing chunk content
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Split long sentence by words
            words = sentence.split()
            temp_chunk = ""
            for word in words:
                if temp_chunk and len(temp_chunk) + len(word) + 1 > max_chunk_size:
                    chunks.append(temp_chunk)
                    temp_chunk = ""
                if temp_chunk:
                    temp_chunk += " " + word
                else:
                    temp_chunk = word

            if temp_chunk:
                current_chunk = temp_chunk
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    # Add any remaining content
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
