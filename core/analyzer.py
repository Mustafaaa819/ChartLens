"""core/analyzer.py — Async orchestrator for the full Map-Reduce extraction pipeline."""
import asyncio
import logging
from pathlib import Path

from core.chunker import chunk_pages
from core.claude_client import extract_medical_events
from core.pdf_extractor import extract_text_by_page

logger = logging.getLogger(__name__)


async def _tracked_chunk(coro, chunk_index: int, total: int, callback) -> dict:
    """Await a chunk extraction coroutine then fire the progress callback."""
    result = await coro
    if callback is not None:
        await callback(f"Extracted chunk {chunk_index} of {total}")
    return result


async def analyze_case(pdf_path: str, progress_callback=None) -> dict:
    """Run the full extraction pipeline for a single case PDF.

    Steps:
        1. extract_text_by_page — raw text per page from the PDF.
        2. chunk_pages — group pages into parallel-processable chunks.
        3. asyncio.gather — run extract_medical_events on all chunks concurrently.
        4. Merge all events from successful chunks into one flat list.

    Args:
        pdf_path: Absolute path string to the PDF file on disk.
        progress_callback: Optional async callable(message: str). Called after
            chunking and after each chunk completes. Caller must not raise.

    Returns:
        On success:
            {
                "events": list[dict],
                "total_chunks": int,
                "successful_chunks": int,
                "failed_chunks": int,
                "failed_chunk_indexes": list[int],
                "total_events": int,
            }
        On catastrophic failure (exception before gather):
            Same keys as above, all zeroed, plus "error": str.
    """
    try:
        pages = extract_text_by_page(Path(pdf_path))
        if not pages:
            return _empty_result(error="PDF text extraction returned no pages.")

        chunks = chunk_pages(pages)
        if not chunks:
            return _empty_result(error="Page chunking produced no chunks.")

        logger.info(
            "analyze_case: %d pages → %d chunks | %s",
            len(pages),
            len(chunks),
            Path(pdf_path).name,
        )

        if progress_callback is not None:
            await progress_callback(f"Starting extraction: {len(chunks)} chunks found")

        # extract_medical_events is synchronous — run all chunks in parallel via threads
        total = len(chunks)
        tasks = [
            _tracked_chunk(
                asyncio.to_thread(extract_medical_events, chunk),
                chunk["chunk_index"],
                total,
                progress_callback,
            )
            for chunk in chunks
        ]
        raw_results: list[dict] = await asyncio.gather(*tasks)

        successful: list[dict] = []
        failed_indexes: list[int] = []

        for result in raw_results:
            chunk_index: int = result.get("chunk_index", -1)
            notes: str = result.get("extraction_notes", "")
            # A chunk is failed only when events are empty AND notes signal an API/parse error.
            # Empty events with no error note = legitimate gap in medical records.
            if not result["events"] and "failed" in notes.lower():
                failed_indexes.append(chunk_index)
                logger.warning("analyze_case: chunk %d failed — %s", chunk_index, notes)
            else:
                successful.append(result)

        all_events: list[dict] = []
        for result in successful:
            all_events.extend(result["events"])

        logger.info(
            "analyze_case complete: %d/%d chunks ok, %d events extracted",
            len(successful),
            len(chunks),
            len(all_events),
        )

        return {
            "events": all_events,
            "total_chunks": len(chunks),
            "successful_chunks": len(successful),
            "failed_chunks": len(failed_indexes),
            "failed_chunk_indexes": failed_indexes,
            "total_events": len(all_events),
        }

    except Exception as exc:
        logger.error("analyze_case catastrophic failure — %s", exc)
        return _empty_result(error=str(exc))


def _empty_result(error: str = "") -> dict:
    """Return a zeroed result dict, with an optional error key."""
    result: dict = {
        "events": [],
        "total_chunks": 0,
        "successful_chunks": 0,
        "failed_chunks": 0,
        "failed_chunk_indexes": [],
        "total_events": 0,
    }
    if error:
        result["error"] = error
    return result
