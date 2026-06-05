"""
End-to-end pipeline test script.
Run with: python tests/test_pipeline.py

Exercises the full ChartLens processing chain on a real PDF and
prints a human-readable summary at the end.
"""

# load_dotenv() must run before any import that touches settings/env vars
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import sys
from pathlib import Path

# Make sure the project root is on sys.path when running from any directory
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.pdf_extractor import extract_text_by_page
from core.chunker import chunk_pages
from core.analyzer import analyze_case
from core.chronology_builder import build_chronology
from core.inconsistency_detector import detect_case_inconsistencies
from core.report_generator import generate_pdf_report, generate_excel_report

# ---------------------------------------------------------------------------
# Config — change these to point at a real PDF before running
# ---------------------------------------------------------------------------

PDF_PATH = "C:/Users/hp/Downloads/test_file.pdf"
OUTPUT_PDF = "test_output_report.pdf"
OUTPUT_XLSX = "test_output_report.xlsx"
CASE_DATA = {"case_number": "TEST-001", "client_name": "Test Patient"}

# ---------------------------------------------------------------------------
# Logging — INFO level so pipeline messages are visible
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_pipeline")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def _run_pipeline() -> None:
    """Execute every pipeline stage in sequence, printing progress."""

    # ------------------------------------------------------------------
    # 1. PDF extraction
    # ------------------------------------------------------------------
    _separator("STEP 1 — PDF Extraction")
    print(f"  PDF: {PDF_PATH}")

    pdf_path = Path(PDF_PATH)
    if not pdf_path.exists():
        _fail(f"PDF not found at '{PDF_PATH}'")
        _fail("Put a test PDF at that path and re-run.")
        sys.exit(1)

    pages = extract_text_by_page(pdf_path)
    if not pages:
        _fail("extract_text_by_page returned no pages — invalid or scanned PDF?")
        sys.exit(1)

    total_pages = len(pages)
    _ok(f"Extracted {total_pages} pages")

    # ------------------------------------------------------------------
    # 2. Chunking
    # ------------------------------------------------------------------
    _separator("STEP 2 — Chunking")

    chunks = chunk_pages(pages)
    if not chunks:
        _fail("chunk_pages produced no chunks")
        sys.exit(1)

    total_chunks = len(chunks)
    _ok(f"{total_pages} pages → {total_chunks} chunks (chunk_size=40)")

    # ------------------------------------------------------------------
    # 3. Analysis (calls Claude API — parallel chunk extraction)
    # ------------------------------------------------------------------
    _separator("STEP 3 — AI Extraction via analyze_case() [Claude API]")
    print("  This may take 30–120 seconds depending on PDF size …")

    try:
        analysis_result = await analyze_case(PDF_PATH)
    except Exception as exc:
        _fail(f"analyze_case raised an unexpected exception: {exc}")
        sys.exit(1)

    if "error" in analysis_result:
        _fail(f"analyze_case returned error: {analysis_result['error']}")
        sys.exit(1)

    _ok(
        f"Extraction complete — {analysis_result['successful_chunks']}/{analysis_result['total_chunks']} "
        f"chunks OK, {analysis_result['failed_chunks']} failed"
    )
    _ok(f"Total events extracted: {analysis_result['total_events']}")

    # ------------------------------------------------------------------
    # 4. Build chronology
    # ------------------------------------------------------------------
    _separator("STEP 4 — Chronology Builder")

    chronology = build_chronology(analysis_result)
    if "error" in chronology:
        _fail(f"build_chronology returned error: {chronology['error']}")
        sys.exit(1)

    _ok(f"Dated events in chronology : {chronology['total_events']}")
    _ok(f"Undated events (no date)   : {chronology['undated_count']}")
    _ok(f"Total billed               : ${chronology['total_billed']:,.2f}")
    _ok(f"Total paid                 : ${chronology['total_paid']:,.2f}")
    if chronology["date_range_start"]:
        _ok(
            f"Date range                 : {chronology['date_range_start']} "
            f"→ {chronology['date_range_end']}"
        )

    # ------------------------------------------------------------------
    # 5. Inconsistency detection (calls Claude API)
    # ------------------------------------------------------------------
    _separator("STEP 5 — Inconsistency Detection [Claude API]")
    print("  Sending chronology summary to Claude …")

    try:
        inconsistencies = detect_case_inconsistencies(chronology)
    except Exception as exc:
        _fail(f"detect_case_inconsistencies raised: {exc}")
        sys.exit(1)

    if "error" in inconsistencies:
        _fail(f"detect_case_inconsistencies returned error: {inconsistencies['error']}")
        sys.exit(1)

    _ok(f"Total inconsistencies      : {inconsistencies['total_inconsistencies']}")
    _ok(f"High-severity count        : {inconsistencies['high_severity_count']}")
    _ok(f"Overall risk assessment    : {inconsistencies.get('overall_risk_assessment', 'N/A')}")

    # ------------------------------------------------------------------
    # 6. PDF report
    # ------------------------------------------------------------------
    _separator("STEP 6 — PDF Report Generation")

    pdf_result = generate_pdf_report(CASE_DATA, chronology, inconsistencies, OUTPUT_PDF)
    if pdf_result is None:
        _fail("generate_pdf_report returned None — check logs above")
        sys.exit(1)
    _ok(f"PDF report written: {pdf_result}")

    # ------------------------------------------------------------------
    # 7. Excel report
    # ------------------------------------------------------------------
    _separator("STEP 7 — Excel Report Generation")

    xlsx_result = generate_excel_report(CASE_DATA, chronology, inconsistencies, OUTPUT_XLSX)
    if xlsx_result is None:
        _fail("generate_excel_report returned None — check logs above")
        sys.exit(1)
    _ok(f"Excel report written: {xlsx_result}")

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    _separator("PIPELINE SUMMARY")
    print(f"  PDF input             : {PDF_PATH}")
    print(f"  Total pages           : {total_pages}")
    print(f"  Total chunks          : {total_chunks}")
    print(f"  Total events extracted: {analysis_result['total_events']}")
    print(f"  Undated events        : {chronology['undated_count']}")
    print(f"  Total billed          : ${chronology['total_billed']:,.2f}")
    print(f"  Total paid            : ${chronology['total_paid']:,.2f}")
    print(f"  Total inconsistencies : {inconsistencies['total_inconsistencies']}")
    print(f"  High severity         : {inconsistencies['high_severity_count']}")
    print(f"  Overall risk          : {inconsistencies.get('overall_risk_assessment', 'N/A')}")
    print(f"  PDF report            : {pdf_result}")
    print(f"  Excel report          : {xlsx_result}")
    print()
    _ok("All pipeline stages completed successfully.")
    print()


def main() -> None:
    asyncio.run(_run_pipeline())


if __name__ == "__main__":
    main()
