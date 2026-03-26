"""
AI Analyzer Worker — Phase 4
Consumes lead:collected, extracts structured intelligence, publishes to lead:analyzed.

LLM backend: Google Gemini (via google-generativeai SDK).
Supports two auth modes:
  1. GCP / Vertex AI — set GCP_PROJECT_ID + GCP_LOCATION, use Application Default Credentials
  2. Direct API key  — set GEMINI_API_KEY (from Google AI Studio)
Falls back to deterministic heuristics when no credentials are configured.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from random import uniform

from backend.core.config import settings
from backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)

# ── Gemini client initialisation ─────────────────────────────────────────────

_gemini_client = None


def _get_gemini_client():
    """
    Lazily initialise Gemini client.
    Returns the model or None if no credentials are configured.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    try:
        import google.generativeai as genai  # type: ignore

        if settings.GEMINI_API_KEY:
            # Option 2: Direct API key (simpler, works outside GCP)
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _gemini_client = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info("Gemini client initialised with API key (model: %s)", settings.GEMINI_MODEL)
        elif settings.GCP_PROJECT_ID:
            # Option 1: Vertex AI via Application Default Credentials
            import vertexai  # type: ignore
            from vertexai.generative_models import GenerativeModel  # type: ignore

            vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
            _gemini_client = GenerativeModel(settings.GEMINI_MODEL)
            logger.info(
                "Gemini client initialised via Vertex AI (project: %s, model: %s)",
                settings.GCP_PROJECT_ID,
                settings.GEMINI_MODEL,
            )
        else:
            logger.warning(
                "No Gemini credentials configured (set GEMINI_API_KEY or GCP_PROJECT_ID). "
                "Falling back to deterministic heuristics."
            )
    except ImportError as exc:
        logger.warning("google-generativeai not installed (%s). Using heuristics.", exc)

    return _gemini_client


# ── Prompt ────────────────────────────────────────────────────────────────────

_ANALYSIS_PROMPT = """\
You are a B2B sales intelligence analyst. Analyse the following demand signal text and extract structured data.

Signal: "{signal}"

Return ONLY a valid JSON object (no markdown, no extra text) with exactly these fields:
{{
  "intent": <float 0.0-1.0, how strongly they intend to buy/hire>,
  "urgency": <float 0.0-1.0, how urgently they need it>,
  "budget": <float 0.0-1.0, likelihood they have budget>,
  "category": <one of: "saas", "fintech", "healthtech", "edtech", "logistics", "general">,
  "estimated_project_size": <one of: "small", "medium", "large">,
  "outreach_angle": <short string, 1 sentence: best angle to approach this lead>
}}
"""


async def _analyze_with_gemini(text: str) -> dict:
    """Call Gemini API to analyse a signal. Returns parsed dict or raises."""
    client = _get_gemini_client()
    if client is None:
        raise RuntimeError("No Gemini client available")

    prompt = _ANALYSIS_PROMPT.format(signal=text)

    # Handle both google-generativeai and Vertex AI GenerativeModel interfaces
    try:
        if hasattr(client, "generate_content_async"):
            response = await client.generate_content_async(prompt)
        else:
            # Vertex AI model may not have async; run in thread
            import asyncio

            response = await asyncio.get_event_loop().run_in_executor(
                None, client.generate_content, prompt
            )

        raw = response.text.strip()
        # Strip markdown code fences if model returned them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise


# ── Heuristic fallback ────────────────────────────────────────────────────────

def _heuristic_analysis(text: str) -> dict:
    """
    Deterministic heuristic analysis — used when Gemini is not configured.
    Suitable for development / demo environments.
    """
    lower = text.lower()
    intent = round(
        uniform(0.6, 1.0)
        if any(w in lower for w in ["need", "looking", "hire", "build"])
        else uniform(0.3, 0.6),
        2,
    )
    urgency = round(
        uniform(0.5, 1.0)
        if any(w in lower for w in ["asap", "urgent", "6 weeks", "immediately"])
        else uniform(0.2, 0.5),
        2,
    )
    budget = round(
        uniform(0.5, 0.9)
        if any(w in lower for w in ["budget", "funded", "series", "million", "$"])
        else uniform(0.2, 0.5),
        2,
    )
    category = (
        "saas" if "saas" in lower
        else "fintech" if "fintech" in lower
        else "healthtech" if "health" in lower
        else "edtech" if "edtech" in lower or "learn" in lower
        else "logistics" if "logistics" in lower or "delivery" in lower
        else "general"
    )
    return {
        "intent": intent,
        "urgency": urgency,
        "budget": budget,
        "category": category,
        "estimated_project_size": "medium",
        "outreach_angle": "Highlight relevant case studies and fast delivery timeline.",
    }


# ── Public API ─────────────────────────────────────────────────────────────────

async def analyze_signal(text: str) -> dict:
    """
    Analyse a raw demand-signal text.
    Tries Gemini first; falls back to heuristics on any failure.
    Returns: { intent, urgency, budget, category, estimated_project_size, outreach_angle }
    """
    try:
        result = await _analyze_with_gemini(text)
        result.setdefault("estimated_project_size", "medium")
        result.setdefault("outreach_angle", "")
        logger.info("Gemini analysis OK — category=%s intent=%.2f", result.get("category"), result.get("intent", 0))
        return result
    except Exception as exc:
        logger.warning("Gemini unavailable (%s) — using heuristics", exc)
        return _heuristic_analysis(text)


async def run_analyzer(last_id: str = "0") -> list[str]:
    """
    Consume events from lead:collected, analyse each, publish to lead:analyzed.
    Returns list of published event IDs.
    """
    events = await redis_client.consume(settings.STREAM_COLLECTED, last_id=last_id)
    published: list[str] = []

    for event_id, data in events:
        text = data.get("text", "")
        analysis = await analyze_signal(text)

        enriched = {
            **data,
            "analysis": json.dumps(analysis),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event_id,
            "ai_provider": "gemini" if _gemini_client is not None else "heuristic",
        }
        new_id = await redis_client.publish(settings.STREAM_ANALYZED, enriched)
        published.append(new_id)

    return published
