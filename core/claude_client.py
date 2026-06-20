"""
core/claude_client.py — The ONLY module that calls the Anthropic API.

All Claude API calls go through here. No other file imports anthropic directly.
"""

import json
import logging
import re

import anthropic

from config import get_settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client() -> anthropic.Anthropic:
    """Create a fresh Anthropic client using the API key from settings."""
    return anthropic.Anthropic(api_key=get_settings().ANTHROPIC_API_KEY)


def _parse_json_response(text: str) -> dict:
    """Strip markdown code fences if present, then parse as JSON.

    Claude sometimes wraps JSON in ```json ... ``` even when told not to.
    This ensures we always get clean JSON regardless.
    """
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1)
    elif text.startswith("```"):
        # Truncated response (hit max_tokens mid-generation): only the opening
        # fence exists, so the closing-fence regex above can't match. Strip
        # just the opening marker and any trailing fence if it happens to be there.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    return json.loads(text.strip())


def _extract_text_from_response(response: anthropic.types.Message) -> str:
    """Return the text of the first text-type content block.

    response.content can include non-text blocks (e.g. thinking blocks)
    before or alongside the text block, so content[0] is not reliable.
    """
    for block in response.content:
        if block.type == "text":
            return block.text
    raise ValueError(
        "No text block found in response.content. "
        f"Block types present: {[block.type for block in response.content]}"
    )


def _build_extraction_prompt(start_page: int, end_page: int, chunk_text: str) -> str:
    """Build the medical event extraction prompt from CLAUDE.md Section 16."""
    return f"""You are a medical record extraction specialist for personal injury law cases.

Extract ALL medical events from the following medical record text.
Return ONLY a valid JSON object. No prose. No explanation. No markdown.

Required JSON format:
{{
  "events": [
    {{
      "date": "YYYY-MM-DD or null if not found",
      "provider_name": "Doctor or facility name",
      "provider_type": "Hospital/Clinic/Specialist/Pharmacy/etc",
      "visit_type": "Emergency/Follow-up/Consultation/Procedure/etc",
      "diagnosis": ["list of diagnoses as strings"],
      "icd_codes": ["list of ICD-10 codes if present, else empty array"],
      "treatment": "Description of treatment, medications, procedures",
      "billed_amount": 0.00,
      "paid_amount": 0.00,
      "page_numbers": [list of page numbers where this event appears],
      "confidence": "high/medium/low",
      "notes": "Any ambiguity or extraction uncertainty"
    }}
  ],
  "extraction_notes": "Any overall notes about this chunk"
}}

Rules:
- Use null for any field where data is not present. Never guess.
- Dates must be YYYY-MM-DD format. If only month/year known, use first of month.
- Dollar amounts must be floats. If not found, use 0.00.
- Include page numbers for every event — this is mandatory for lawyer verification.
- If multiple events occur in one visit, create separate event objects for each.
- Confidence is high if all fields are clearly stated, medium if some inferred,
  low if heavily uncertain.

Medical record text (pages {start_page}–{end_page}):
{chunk_text}"""


def _build_inconsistency_prompt(chronology_summary: str) -> str:
    """Build the inconsistency detection prompt."""
    return f"""You are a medical record analyst for personal injury cases.
Review this medical chronology and identify inconsistencies.
Return ONLY valid JSON, no prose, no markdown.

Find these specific inconsistency types:
- Prior condition denial (patient denied condition that earlier records confirm)
- Treatment gaps (unexplained gaps of 60+ days between treatments)
- Billing anomalies (billed amounts that seem incorrect or duplicated)
- Provider statement conflicts (conflicting clinical findings between providers)
- Date anomalies (events recorded out of logical sequence)

Required JSON format:
{{
  "inconsistencies": [
    {{
      "inconsistency_type": "string",
      "severity": "low|medium|high",
      "description": "string",
      "date_1": "YYYY-MM-DD or null",
      "date_2": "YYYY-MM-DD or null",
      "page_references": [list of ints],
      "recommendation": "string"
    }}
  ],
  "overall_risk_assessment": "low|medium|high",
  "notes": "string"
}}

Chronology to analyze:
{chronology_summary}"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_medical_events(chunk: dict) -> dict:
    """Extract structured medical events from a single text chunk.

    Args:
        chunk: A chunk dict from chunker.chunk_pages(), with keys:
               chunk_index, start_page, end_page, text, page_count, total_chars.

    Returns:
        Parsed JSON dict with an "events" list on success.
        Fallback dict with empty events and error note on any failure.
        Never raises an exception.
    """
    chunk_index: int = chunk["chunk_index"]
    try:
        prompt = _build_extraction_prompt(
            start_page=chunk["start_page"],
            end_page=chunk["end_page"],
            chunk_text=chunk["text"],
        )

        client = _get_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )

        logger.debug(
            "extract_medical_events chunk %d output_tokens used: %d (max_tokens=16000)",
            chunk_index,
            response.usage.output_tokens,
        )
        if response.stop_reason == "max_tokens":
            raise RuntimeError(
                f"Response truncated at max_tokens for chunk {chunk_index} — "
                f"output_tokens={response.usage.output_tokens}"
            )
        logger.debug(
            "extract_medical_events chunk %d response block types: %s",
            chunk_index,
            [block.type for block in response.content],
        )
        raw_text = _extract_text_from_response(response)
        logger.debug(
            "extract_medical_events chunk %d raw_text (first 500 chars): %r",
            chunk_index,
            raw_text[:500],
        )
        logger.debug(
            "extract_medical_events chunk %d raw_text length: %d",
            chunk_index,
            len(raw_text),
        )
        data = _parse_json_response(raw_text)

        if "events" not in data or not isinstance(data["events"], list):
            raise ValueError(
                f"Response missing 'events' list. Keys found: {list(data.keys())}"
            )

        data["chunk_index"] = chunk_index
        logger.info(
            "Chunk %d extracted %d event(s) (pages %d–%d)",
            chunk_index,
            len(data["events"]),
            chunk["start_page"],
            chunk["end_page"],
        )
        return data

    except Exception as exc:
        error_msg = f"Extraction failed: {exc}"
        logger.error("extract_medical_events chunk %d — %s", chunk_index, error_msg)
        return {
            "events": [],
            "extraction_notes": error_msg,
            "chunk_index": chunk_index,
        }


def detect_inconsistencies(chronology_summary: str) -> dict:
    """Scan a merged chronology summary for medical record inconsistencies.

    Args:
        chronology_summary: Plain-text summary of the merged chronology.
                            NOT the full PDF text — only the summarised events.

    Returns:
        Parsed JSON dict with an "inconsistencies" list on success.
        Fallback dict on any failure. Never raises an exception.
    """
    try:
        prompt = _build_inconsistency_prompt(chronology_summary)

        client = _get_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        logger.debug(
            "detect_inconsistencies output_tokens used: %d (max_tokens=8000)",
            response.usage.output_tokens,
        )
        if response.stop_reason == "max_tokens":
            raise RuntimeError(
                f"Response truncated at max_tokens for inconsistency detection — "
                f"output_tokens={response.usage.output_tokens}"
            )
        logger.debug(
            "detect_inconsistencies response block types: %s",
            [block.type for block in response.content],
        )
        raw_text = _extract_text_from_response(response)
        logger.debug(
            "detect_inconsistencies raw_text (first 500 chars): %r",
            raw_text[:500],
        )
        logger.debug(
            "detect_inconsistencies raw_text length: %d",
            len(raw_text),
        )
        data = _parse_json_response(raw_text)

        if "inconsistencies" not in data or not isinstance(
            data["inconsistencies"], list
        ):
            raise ValueError(
                f"Response missing 'inconsistencies' list. Keys: {list(data.keys())}"
            )

        logger.info(
            "Inconsistency detection found %d issue(s), risk=%s",
            len(data["inconsistencies"]),
            data.get("overall_risk_assessment", "unknown"),
        )
        return data

    except Exception as exc:
        error_msg = f"Detection failed: {exc}"
        logger.error("detect_inconsistencies — %s", error_msg)
        return {
            "inconsistencies": [],
            "overall_risk_assessment": "unknown",
            "notes": error_msg,
        }


def ping_claude() -> bool:
    """Send a minimal request to verify the Anthropic API key and connection.

    Returns:
        True if the API responds with "PONG", False on any failure.
    """
    try:
        client = _get_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Reply with only the word PONG"}],
        )
        reply = _extract_text_from_response(response).strip().upper()
        return "PONG" in reply
    except Exception as exc:
        logger.error("ping_claude failed — %s", exc)
        return False
