"""
Inconsistency detector: builds a plain-text chronology summary and calls
Claude to flag contradictions. Pure orchestration — no DB, no direct
Anthropic imports.
"""

import logging

from core.claude_client import detect_inconsistencies

logger = logging.getLogger(__name__)


def _build_summary_line(event: dict) -> str:
    """Format a single event dict as one human-readable summary line."""
    date = event.get("date") or "Unknown date"
    provider = event.get("provider_name") or "Unknown provider"
    visit_type = event.get("visit_type") or "Unknown visit"

    diagnoses = event.get("diagnosis") or []
    diagnosis_str = ", ".join(diagnoses) if diagnoses else "No diagnosis recorded"

    billed = event.get("billed_amount") or 0.0
    return f"{date} | {provider} | {visit_type} | {diagnosis_str} | Billed: ${billed:.2f}"


def detect_case_inconsistencies(chronology_result: dict) -> dict:
    """
    Run the Claude inconsistency detection pass on a built chronology.

    Args:
        chronology_result: The dict returned by build_chronology().
                           Uses the "chronology" key (sorted, deduped events).

    Returns:
        The dict from detect_inconsistencies() enriched with:
          total_inconsistencies, high_severity_count,
          case_date_range_start, case_date_range_end.
        On catastrophic failure returns a dict with "error" key and
        safe empty defaults.
    """
    _empty_result = {
        "inconsistencies": [],
        "overall_risk_assessment": "unknown",
        "notes": "",
        "total_inconsistencies": 0,
        "high_severity_count": 0,
        "case_date_range_start": chronology_result.get("date_range_start"),
        "case_date_range_end": chronology_result.get("date_range_end"),
    }

    try:
        chronology: list[dict] = chronology_result.get("chronology", [])

        if not chronology:
            logger.info("detect_case_inconsistencies: empty chronology — skipping Claude call")
            _empty_result["notes"] = "No dated events in chronology; inconsistency check skipped."
            return _empty_result

        summary_lines = [_build_summary_line(event) for event in chronology]
        chronology_summary = "\n".join(summary_lines)

        result: dict = detect_inconsistencies(chronology_summary)

        inconsistencies: list[dict] = result.get("inconsistencies") or []
        high_count = sum(
            1 for item in inconsistencies if item.get("severity") == "high"
        )

        result["total_inconsistencies"] = len(inconsistencies)
        result["high_severity_count"] = high_count
        result["case_date_range_start"] = chronology_result.get("date_range_start")
        result["case_date_range_end"] = chronology_result.get("date_range_end")

        logger.info(
            "Inconsistency detection complete: %d total, %d high-severity",
            len(inconsistencies),
            high_count,
        )
        return result

    except Exception as exc:
        logger.exception("Catastrophic failure in detect_case_inconsistencies: %s", exc)
        _empty_result["error"] = str(exc)
        return _empty_result
