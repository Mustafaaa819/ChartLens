"""
Chronology builder: sorts, deduplicates, and summarizes extracted medical events.
Pure data transformation — no DB, no Claude API calls.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}

_DATE_FORMAT = "%Y-%m-%d"


def build_chronology(analysis_result: dict) -> dict:
    """
    Take the dict returned by analyze_case() and produce a clean chronology.

    Returns a dict with keys: chronology, undated_events, total_events,
    undated_count, total_billed, total_paid, date_range_start, date_range_end.
    On catastrophic failure returns a dict with an "error" key.
    """
    try:
        raw_events: list[dict] = analysis_result.get("events", [])

        dated: list[tuple[datetime, dict]] = []
        undated: list[dict] = []

        for event in raw_events:
            date_str = event.get("date")
            if not date_str:
                undated.append(event)
                continue

            try:
                parsed = datetime.strptime(date_str, _DATE_FORMAT)
                dated.append((parsed, event))
            except (ValueError, TypeError):
                logger.warning("Unparseable date '%s' — moving event to undated_events", date_str)
                undated.append(event)

        # Sort ascending by date
        dated.sort(key=lambda x: x[0])

        # Deduplicate: same (date, provider_name, visit_type) → keep higher confidence
        seen: dict[tuple, dict] = {}
        for parsed_dt, event in dated:
            key = (
                parsed_dt.date(),
                (event.get("provider_name") or "").strip().lower(),
                (event.get("visit_type") or "").strip().lower(),
            )
            if key in seen:
                existing = seen[key]
                existing_rank = CONFIDENCE_RANK.get(existing.get("confidence", "low"), 1)
                incoming_rank = CONFIDENCE_RANK.get(event.get("confidence", "low"), 1)
                if incoming_rank > existing_rank:
                    logger.warning(
                        "Duplicate event dropped: date=%s provider='%s' visit_type='%s' "
                        "(kept confidence=%s, dropped confidence=%s)",
                        key[0], event.get("provider_name"), event.get("visit_type"),
                        event.get("confidence"), existing.get("confidence"),
                    )
                    seen[key] = event
                else:
                    logger.warning(
                        "Duplicate event dropped: date=%s provider='%s' visit_type='%s' "
                        "(kept confidence=%s, dropped confidence=%s)",
                        key[0], existing.get("provider_name"), existing.get("visit_type"),
                        existing.get("confidence"), event.get("confidence"),
                    )
            else:
                seen[key] = event

        # Rebuild sorted list from deduped dict (insertion order preserved in Python 3.7+,
        # but we re-sort to guarantee order after potential replacements)
        deduped_dated: list[tuple[datetime, dict]] = []
        for (date_obj, provider, visit), event in seen.items():
            parsed_dt = datetime.combine(date_obj, datetime.min.time())
            deduped_dated.append((parsed_dt, event))
        deduped_dated.sort(key=lambda x: x[0])

        chronology: list[dict] = []
        total_billed = 0.0
        total_paid = 0.0

        for parsed_dt, event in deduped_dated:
            # Keep date as YYYY-MM-DD string
            normalized = dict(event)
            normalized["date"] = parsed_dt.strftime(_DATE_FORMAT)
            chronology.append(normalized)

            total_billed += float(event.get("billed_amount") or 0.0)
            total_paid += float(event.get("paid_amount") or 0.0)

        date_range_start = chronology[0]["date"] if chronology else None
        date_range_end = chronology[-1]["date"] if chronology else None

        return {
            "chronology": chronology,
            "undated_events": undated,
            "total_events": len(chronology),
            "undated_count": len(undated),
            "total_billed": round(total_billed, 2),
            "total_paid": round(total_paid, 2),
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
        }

    except Exception as exc:
        logger.exception("Catastrophic failure in build_chronology: %s", exc)
        return {"error": str(exc)}
