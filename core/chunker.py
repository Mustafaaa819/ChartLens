"""
core/chunker.py — Groups extracted PDF pages into chunks for parallel Claude API calls.

Part of the Map-Reduce pipeline described in CLAUDE.md Section 7.2.
Each chunk becomes one Claude API call; chunks are processed in parallel via asyncio.
"""

import logging
import math

logger = logging.getLogger(__name__)


def chunk_pages(pages: list[dict], chunk_size: int = 40) -> list[dict]:
    """Group a list of page dicts into fixed-size chunks for parallel processing.

    Args:
        pages: Output of extract_text_by_page() — list of dicts with keys:
               page_number (int), text (str), char_count (int).
        chunk_size: Number of pages per chunk. Defaults to 40.

    Returns:
        List of chunk dicts, each containing:
            chunk_index (int): 0-based index.
            start_page (int): First page number in this chunk (from original PDF).
            end_page (int): Last page number in this chunk (from original PDF).
            page_count (int): Number of pages in this chunk.
            text (str): Combined text with --- PAGE N --- markers before each page.
            total_chars (int): Total character count of combined text.
    """
    if not pages:
        logger.warning("chunk_pages called with empty pages list")
        return []

    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")

    chunks: list[dict] = []

    for chunk_index, offset in enumerate(range(0, len(pages), chunk_size)):
        page_group = pages[offset : offset + chunk_size]

        # Build combined text with mandatory page markers so Claude can return
        # accurate page_numbers in its extraction output.
        parts: list[str] = []
        for page in page_group:
            parts.append(f"--- PAGE {page['page_number']} ---\n{page['text']}\n")
        combined_text = "\n".join(parts)

        chunks.append(
            {
                "chunk_index": chunk_index,
                "start_page": page_group[0]["page_number"],
                "end_page": page_group[-1]["page_number"],
                "page_count": len(page_group),
                "text": combined_text,
                "total_chars": len(combined_text),
            }
        )

    logger.debug(
        "chunk_pages: %d pages → %d chunks (chunk_size=%d)",
        len(pages),
        len(chunks),
        chunk_size,
    )
    return chunks


def estimate_chunks(page_count: int, chunk_size: int = 40) -> dict:
    """Estimate how many chunks a PDF will produce without doing any I/O.

    Args:
        page_count: Total number of pages in the PDF.
        chunk_size: Pages per chunk. Defaults to 40.

    Returns:
        Dict with keys:
            chunk_count (int): Total number of chunks.
            chunk_size (int): Pages per full chunk.
            last_chunk_pages (int): Pages in the final (possibly partial) chunk.
    """
    if page_count < 0:
        raise ValueError(f"page_count must be >= 0, got {page_count}")
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")

    if page_count == 0:
        return {"chunk_count": 0, "chunk_size": chunk_size, "last_chunk_pages": 0}

    chunk_count = math.ceil(page_count / chunk_size)
    remainder = page_count % chunk_size
    last_chunk_pages = remainder if remainder != 0 else chunk_size

    return {
        "chunk_count": chunk_count,
        "chunk_size": chunk_size,
        "last_chunk_pages": last_chunk_pages,
    }


def get_chunk_stats(chunks: list[dict]) -> dict:
    """Return summary statistics over a list of chunks.

    Args:
        chunks: Output of chunk_pages().

    Returns:
        Dict with keys:
            total_chunks (int)
            total_chars (int)
            avg_chars_per_chunk (int): Rounded to nearest integer.
            largest_chunk_chars (int)
            smallest_chunk_chars (int)
    """
    if not chunks:
        return {
            "total_chunks": 0,
            "total_chars": 0,
            "avg_chars_per_chunk": 0,
            "largest_chunk_chars": 0,
            "smallest_chunk_chars": 0,
        }

    char_counts = [c["total_chars"] for c in chunks]
    total_chars = sum(char_counts)

    return {
        "total_chunks": len(chunks),
        "total_chars": total_chars,
        "avg_chars_per_chunk": round(total_chars / len(chunks)),
        "largest_chunk_chars": max(char_counts),
        "smallest_chunk_chars": min(char_counts),
    }
