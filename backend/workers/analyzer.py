"""
workers/analyzer.py — GeminiAnalyzer + AnalysisResult dataclass.

IMPORTANT: Keep shared/models.py open alongside this file — Copilot infers
Lead field names and types from there.

AnalysisResult is the canonical output contract for every analysis call.
All downstream workers (scorer, outreach) consume AnalysisResult fields.

Prompt constants are module-level so Copilot can autocomplete them.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.shared.config import settings
from backend.shared.stream import redis_stream

logger = logging.getLogger(__name__)

# ── Prompt constants ──────────────────────────────────────────────────────────
# Multi-mode classifiers — selected based on mode field in stream event.
# Each mode defines different "is_opportunity" criteria and intent taxonomy.

CLASSIFIER_PROMPT = """\
You are a B2B sales intelligence classifier. Analyse the following demand signal.

Signal text: "{text}"
Source: {source}

Return ONLY a valid JSON object — no markdown, no extra text — with exactly these fields:
{{
  "is_opportunity": <true if this is a genuine B2B buying/evaluation signal, else false>,
  "confidence": <float 0.0-1.0 — how confident you are>,
  "intent": "<buy | evaluate | pain | compare | other>",
  "urgency": "<high | medium | low>",
  "reason": "<one sentence explaining your classification>"
}}

Rules:
- is_opportunity = false if: student project, academic question, general discussion, news article
- is_opportunity = true if: buying intent, vendor comparison, pain point with budget hints, hiring for solution
"""

_CLASSIFIER_PROMPTS: dict[str, str] = {
    "b2b_sales": CLASSIFIER_PROMPT,

    "hiring": """\
You are a talent acquisition intelligence classifier. Analyse the following signal.

Signal text: "{text}"
Source: {source}

Return ONLY a valid JSON object with exactly these fields:
{{
  "is_opportunity": <true if this signal shows a company actively hiring or scaling>,
  "confidence": <float 0.0-1.0>,
  "intent": "<hiring_urgent | hiring_planned | company_growth | other>",
  "urgency": "<high | medium | low>",
  "reason": "<one sentence>"
}}

is_opportunity = true if: job posting, "we're hiring", scaling announcement, Series A/B expansion.
intent = hiring_urgent if explicit open roles; hiring_planned if growth/funding signal.
Urgency = high if roles are open now; medium if planned; low if general growth signal.
""",

    "job_search": """\
You are a job market intelligence classifier. Analyse the following signal.

Signal text: "{text}"
Source: {source}

Return ONLY a valid JSON object with exactly these fields:
{{
  "is_opportunity": <true if this is a genuine job opening or strong employer signal>,
  "confidence": <float 0.0-1.0>,
  "intent": "<open_role | company_signal | culture_signal | compensation_signal | other>",
  "urgency": "<high | medium | low>",
  "reason": "<one sentence>"
}}

is_opportunity = true if: job posting, "we are hiring", remote culture signal, equity/comp mention.
Urgency = high if immediate start or closing soon; medium if active hiring; low if general company signal.
""",

    "opportunity": """\
You are a market intelligence analyst detecting emerging business opportunities.

Signal text: "{text}"
Source: {source}

Return ONLY a valid JSON object with exactly these fields:
{{
  "is_opportunity": <true if this reveals a genuine market gap or rising unmet demand>,
  "confidence": <float 0.0-1.0>,
  "intent": "<market_gap | pain_point | trend | emerging_tech | other>",
  "urgency": "<high | medium | low>",
  "reason": "<one sentence>"
}}

is_opportunity = true if: common pain with no good incumbent solution, growing demand, underserved segment.
Urgency = high if multiple people expressing same pain; medium if single strong signal; low if speculative.
""",
}

# ENRICHMENT_PROMPT: extracts company/contact metadata and outreach draft.
# Run only when is_opportunity = true (saves Gemini quota).
ENRICHMENT_PROMPT = """\
You are a B2B sales researcher. A demand signal has been classified as a genuine opportunity.

Signal text: "{text}"
Author: {author}
Source: {source}
Intent: {intent}
Urgency: {urgency}

Return ONLY a valid JSON object — no markdown, no extra text — with:
{{
  "company_name": "<inferred company name or null>",
  "company_size": "<startup | smb | enterprise | unknown>",
  "industry": "<inferred industry vertical or null>",
  "contact_name": "<author's real name if inferrable, else null>",
  "contact_title": "<inferred job title or null>",
  "icp_fit_score": <int 0-100, how well this matches a typical SaaS B2B ICP>,
  "outreach_draft": "<a concise, non-spammy 2-sentence outreach message referencing their specific pain>"
}}
"""

_ENRICHMENT_PROMPTS: dict[str, str] = {
    "b2b_sales": ENRICHMENT_PROMPT,

    "hiring": """\
You are a talent acquisition researcher. A signal indicates a company is hiring.

Signal text: "{text}"
Author: {author}
Source: {source}
Intent: {intent}
Urgency: {urgency}

Return ONLY a valid JSON object with:
{{
  "company_name": "<company or null>",
  "company_size": "<startup | smb | enterprise | unknown>",
  "industry": "<industry vertical or null>",
  "contact_name": "<hiring manager name if visible>",
  "contact_title": "<inferred title of poster>",
  "icp_fit_score": <int 0-100, attractiveness as a hiring target>,
  "outreach_draft": "<brief, specific message to the hiring manager referencing the role>"
}}
""",

    "job_search": """\
You are a career intelligence researcher. Analyse this job opportunity.

Signal text: "{text}"
Author: {author}
Source: {source}

Return ONLY a valid JSON object with:
{{
  "company_name": "<company or null>",
  "company_size": "<startup | smb | enterprise | unknown>",
  "industry": "<industry vertical or null>",
  "contact_name": "<hiring manager if visible>",
  "contact_title": "<role title being hired for>",
  "icp_fit_score": <int 0-100, strength of opportunity>,
  "outreach_draft": "<brief, personalised application message>"
}}
""",

    "opportunity": """\
You are a market opportunity researcher.

Signal text: "{text}"
Author: {author}
Source: {source}

Return ONLY a valid JSON object with:
{{
  "company_name": "<mentioned company or null>",
  "company_size": "<startup | smb | enterprise | unknown>",
  "industry": "<industry vertical or null>",
  "contact_name": "<author name if relevant>",
  "contact_title": null,
  "icp_fit_score": <int 0-100, significance of this market opportunity>,
  "outreach_draft": "<message to the person expressing the pain, offer to co-explore>"
}}
""",
}


# ── AnalysisResult dataclass ──────────────────────────────────────────────────
# PASTE THIS AS A COMMENT BLOCK at the top of any file that consumes analysis output.
# Workers use this as the return type target.

@dataclass
class AnalysisResult:
    """Full output of GeminiAnalyzer.analyze(). Persisted to Lead table."""

    # From classifier
    is_opportunity: bool = False
    confidence: float = 0.0
    intent: str = "other"              # buy | evaluate | pain | compare | other
    urgency: str = "low"               # high | medium | low
    reason: str = ""

    # From enrichment (only populated when is_opportunity=True)
    company_name: str | None = None
    company_size: str | None = None
    industry: str | None = None
    contact_name: str | None = None
    contact_title: str | None = None
    icp_fit_score: float = 0.0         # 0–100
    outreach_draft: str | None = None

    # Metadata
    model_used: str = ""
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_opportunity": self.is_opportunity,
            "confidence": self.confidence,
            "intent": self.intent,
            "urgency": self.urgency,
            "reason": self.reason,
            "company_name": self.company_name,
            "company_size": self.company_size,
            "industry": self.industry,
            "contact_name": self.contact_name,
            "contact_title": self.contact_title,
            "icp_fit_score": self.icp_fit_score,
            "outreach_draft": self.outreach_draft,
            "model_used": self.model_used,
            "analyzed_at": self.analyzed_at.isoformat(),
            "tokens_used": self.tokens_used,
        }


# ── GeminiAnalyzer ────────────────────────────────────────────────────────────

class GeminiAnalyzer:
    """
    Analyzes raw posts using Gemini.
    Falls back to deterministic heuristics when no credentials are configured.
    """

    def __init__(self) -> None:
        self._model = None
        self._backend: str = "heuristic"

    def _init_model(self) -> None:
        if self._model is not None:
            return
        try:
            import google.generativeai as genai  # type: ignore

            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
                self._backend = "gemini-api"
            elif settings.GCP_PROJECT_ID:
                import vertexai  # type: ignore
                from vertexai.generative_models import GenerativeModel  # type: ignore

                vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
                self._model = GenerativeModel(settings.GEMINI_MODEL)
                self._backend = "vertex-ai"
            else:
                logger.warning("No Gemini credentials — using heuristic fallback.")
        except ImportError:
            logger.warning("google-generativeai not installed — using heuristic fallback.")

    async def analyze(self, text: str, source: str = "", author: str = "", mode: str = "b2b_sales") -> AnalysisResult:
        """Full analysis: classify → enrich (if opportunity). Returns AnalysisResult."""
        self._init_model()

        result = await self._classify(text, source, mode)

        if result.is_opportunity:
            await self._enrich(result, text, source, author, mode)

        return result

    async def _classify(self, text: str, source: str, mode: str = "b2b_sales") -> AnalysisResult:
        if not self._model:
            return self._heuristic_classify(text, mode)

        prompt_template = _CLASSIFIER_PROMPTS.get(mode, CLASSIFIER_PROMPT)
        prompt = prompt_template.format(text=text[:2000], source=source)
        try:
            response = self._model.generate_content(prompt)
            raw = response.text
            data = _parse_json(raw)
            return AnalysisResult(
                is_opportunity=bool(data.get("is_opportunity", False)),
                confidence=float(data.get("confidence", 0.0)),
                intent=str(data.get("intent", "other")),
                urgency=str(data.get("urgency", "low")),
                reason=str(data.get("reason", "")),
                model_used=settings.GEMINI_MODEL,
                tokens_used=_estimate_tokens(prompt + raw),
            )
        except Exception as exc:
            logger.warning("Gemini classify failed: %s — falling back to heuristic", exc)
            return self._heuristic_classify(text, mode)

    async def _enrich(self, result: AnalysisResult, text: str, source: str, author: str, mode: str = "b2b_sales") -> None:
        if not self._model:
            return

        prompt_template = _ENRICHMENT_PROMPTS.get(mode, ENRICHMENT_PROMPT)
        prompt = prompt_template.format(
            text=text[:2000],
            author=author,
            source=source,
            intent=result.intent,
            urgency=result.urgency,
        )
        try:
            response = self._model.generate_content(prompt)
            data = _parse_json(response.text)
            result.company_name = data.get("company_name")
            result.company_size = data.get("company_size")
            result.industry = data.get("industry")
            result.contact_name = data.get("contact_name")
            result.contact_title = data.get("contact_title")
            result.icp_fit_score = float(data.get("icp_fit_score", 0.0))
            result.outreach_draft = data.get("outreach_draft")
            result.tokens_used += _estimate_tokens(prompt + response.text)
        except Exception as exc:
            logger.warning("Gemini enrich failed: %s", exc)

    def _heuristic_classify(self, text: str, mode: str = "b2b_sales") -> AnalysisResult:
        """Deterministic fallback when Gemini is unavailable. Mode-aware."""
        text_lower = text.lower()

        if mode == "hiring":
            hiring_kw = ["hiring", "join our team", "open position", "we're looking for", "apply now"]
            score = sum(1 for kw in hiring_kw if kw in text_lower)
            return AnalysisResult(
                is_opportunity=score >= 1,
                confidence=min(0.4 + score * 0.1, 0.8),
                intent="hiring_urgent" if score >= 2 else "company_growth",
                urgency="high" if score >= 2 else "medium",
                reason="Heuristic: hiring keyword match",
                model_used="heuristic",
            )

        if mode == "job_search":
            job_kw = ["software engineer", "developer", "remote", "full-time", "open role", "job"]
            score = sum(1 for kw in job_kw if kw in text_lower)
            return AnalysisResult(
                is_opportunity=score >= 2,
                confidence=min(0.4 + score * 0.1, 0.8),
                intent="open_role" if score >= 2 else "company_signal",
                urgency="medium",
                reason="Heuristic: job signal keyword match",
                model_used="heuristic",
            )

        if mode == "opportunity":
            gap_kw = ["nobody", "wish there was", "underserved", "gap", "no good tool", "no solution"]
            score = sum(1 for kw in gap_kw if kw in text_lower)
            return AnalysisResult(
                is_opportunity=score >= 1,
                confidence=min(0.3 + score * 0.15, 0.75),
                intent="market_gap" if score >= 2 else "pain_point",
                urgency="high" if score >= 2 else "medium",
                reason="Heuristic: market gap keyword match",
                model_used="heuristic",
            )

        # Default: b2b_sales
        buy_keywords  = ["looking for", "recommend", "need", "hiring", "budget", "urgent", "asap"]
        pain_keywords = ["frustrated", "hate", "broken", "switching from", "replacing"]
        score = sum(1 for kw in buy_keywords if kw in text_lower)
        is_opp = score >= 2
        pain   = any(kw in text_lower for kw in pain_keywords)
        return AnalysisResult(
            is_opportunity=is_opp,
            confidence=min(0.3 + score * 0.1, 0.8),
            intent="pain" if pain else ("buy" if is_opp else "other"),
            urgency="high" if "urgent" in text_lower or "asap" in text_lower else "medium",
            reason="Heuristic match",
            model_used="heuristic",
        )


# ── Stream consumer entry point ───────────────────────────────────────────────

async def run_analyzer(consumer_name: str = "analyzer-1") -> None:
    """
    Consume lead:collected stream, analyze each post, publish to lead:analyzed.
    Designed to run as a long-lived process or Celery task.
    """
    analyzer = GeminiAnalyzer()
    group = "analyzers"
    stream = settings.STREAM_COLLECTED

    await redis_stream.ensure_group(stream, group)
    logger.info("Analyzer consumer '%s' started, reading from '%s'", consumer_name, stream)

    while True:
        events = await redis_stream.consume_group(stream, group, consumer_name, count=5)
        for event in events:
            try:
                text   = event.get("body") or event.get("text") or ""
                source = event.get("source", "")
                author = event.get("author", "")
                mode   = event.get("mode", "b2b_sales")  # injected by pipeline from profile
                result = await analyzer.analyze(text, source, author, mode)

                payload = {**event.data, **result.to_dict()}
                await redis_stream.publish(settings.STREAM_ANALYZED, payload)
                await redis_stream.ack(stream, group, event.event_id)
                logger.info("Analyzed event %s: is_opportunity=%s", event.event_id, result.is_opportunity)
                # Emit domain event
                from backend.events.emitter import emit
                lead_id = event.get("id", str(uuid.uuid4()))
                emit("lead_enriched", {
                    "id": lead_id,
                    "source": event.get("source"),
                    "is_opportunity": result.is_opportunity,
                })
            except Exception as exc:
                logger.error("Analyzer failed on event %s: %s", event.event_id, exc)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict[str, Any]:
    """Extract JSON from Gemini response, handling markdown code fences."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(cleaned)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)
