#!/usr/bin/env python3
"""
tests/test_day1_gemini_smoke.py
Day 1 Evening — Gemini Smoke Test + Handoff Report Generator

3 test cases verifying the full Gemini wiring is live.
Run: python tests/test_day1_gemini_smoke.py

EXIT CODES:
  0 = 3/3 passed — safe to commit
  1 = partial pass — investigate before committing
  2 = all failed — DO NOT commit, check GEMINI_API_KEY
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

# ── ANSI ─────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
CYAN   = "\033[96m"; BOLD = "\033[1m"; RESET = "\033[0m"
PASS_  = f"{GREEN}✅ PASS{RESET}"; FAIL_ = f"{RED}❌ FAIL{RESET}"
WARN_  = f"{YELLOW}⚠️  WARN{RESET}"

# ── 3 deterministic test inputs ───────────────────────────────────────────────
# Each represents a real source type Lead-iq must handle.
# Expected outputs are conservative — we check shape + invariants, not values.

TEST_CASES = [
    {
        "id"    : "TC-01",
        "label" : "HN Show HN post — SaaS tool launch",
        "source": "hacker_news",
        "url"   : "https://news.ycombinator.com/item?id=tc01",
        "text"  : """
            Show HN: We built Syncly – real-time meeting notes that sync to Notion
            Hey HN, we're a 2-person team from Bangalore. We spent 6 months building
            Syncly after getting frustrated with manual note-taking during client calls.
            We process audio, extract action items, and push them to Notion in < 5s.
            We're looking for our first 50 beta users. Pricing: $19/month.
            Tech stack: Whisper, GPT-4, Notion API. Email: founders@syncly.in
            We're registered as Syncly Technologies Pvt Ltd on MCA21.
        """,
        "expect": {
            "is_opportunity"     : True,
            "intent_one_of"      : ["buy", "evaluate", "other"],
            "confidence_min"     : 0.50,
            "company_name_notnull": True,
            "india_signals_has"  : ["Pvt Ltd", "Bangalore", "MCA21"],
            "email_extracted"    : "founders@syncly.in",
        },
    },
    {
        "id"    : "TC-02",
        "label" : "GitHub README — open source devtool with hiring signal",
        "source": "github_profile",
        "url"   : "https://github.com/acme-corp/devtools",
        "text"  : """
            # DevTools by Acme Corp
            Production-grade observability for distributed systems.
            We are hiring: Senior Backend Engineer (Remote, India preferred).
            Stack: Go, Kubernetes, ClickHouse, OpenTelemetry.
            Company: Acme Corp, Series B ($14M raised), 50-200 employees.
            We replace Datadog for teams that hate per-seat pricing.
            Contact: careers@acmecorp.io
        """,
        "expect": {
            "is_opportunity"     : True,
            "intent_one_of"      : ["hire", "pain", "evaluate", "buy"],
            "confidence_min"     : 0.55,
            "company_name_notnull": True,
            "pain_point_notnull" : True,   # "hate per-seat pricing"
            "email_extracted"    : "careers@acmecorp.io",
        },
    },
    {
        "id"    : "TC-03",
        "label" : "Noise post — no buying signal",
        "source": "hacker_news",
        "url"   : "https://news.ycombinator.com/item?id=tc03",
        "text"  : """
            Ask HN: What's your favourite keyboard layout?
            I recently switched from QWERTY to Colemak and my WPM dropped from 90 to 40.
            Anyone else go through this? How long did it take to recover?
            Posted by: kbfanatic99
        """,
        "expect": {
            "is_opportunity"     : False,  # hard requirement — no false positive
            "confidence_max"     : 0.45,   # must be low confidence
        },
    },
]


# ── Result container ──────────────────────────────────────────────────────────
class TestResult:
    def __init__(self, tc: dict):
        self.tc         = tc
        self.passed     = False
        self.assertions = []   # list of (name, passed, detail)
        self.raw_result = None
        self.tokens_used= 0
        self.latency_ms = 0
        self.error      = None

    def assert_check(self, name: str, passed: bool, detail: str) -> None:
        self.assertions.append((name, passed, detail))

    def verdict(self) -> str:
        if self.error:
            return "FAIL"
        failed = [a for a in self.assertions if not a[1]]
        if not failed:
            return "PASS"
        critical_fails = [a for a in failed if "is_opportunity" in a[0] or "notnull" in a[0]]
        return "FAIL" if critical_fails else "WARN"


# ── Core runner ───────────────────────────────────────────────────────────────
async def run_test_case(tc: dict) -> TestResult:
    result = TestResult(tc)
    t0 = time.monotonic()

    try:
        # Import here so missing deps show clearly
        from backend.llm.gemini_service import extract_lead

        raw = await extract_lead(
            markdown_content=tc["text"],
            source=tc["source"],
            url=tc["url"],
        )
        result.latency_ms = int((time.monotonic() - t0) * 1000)

        # ── Guard: None means pipeline correctly routed to DLQ ───────────
        if raw is None:
            result.error = "extract_lead() returned None — check Gemini API key and budget"
            return result

        result.raw_result = raw
        result.tokens_used = raw.get("tokens_used", 0)
        exp = tc["expect"]

        # ── Assertion 1: is_opportunity matches expectation ───────────────
        actual_opp = raw.get("is_opportunity", None)
        exp_opp    = exp.get("is_opportunity")
        if exp_opp is not None:
            ok = (actual_opp == exp_opp)
            result.assert_check(
                "is_opportunity",
                ok,
                f"expected={exp_opp}  got={actual_opp}"
            )

        # ── Assertion 2: intent is a known value ─────────────────────────
        valid_intents = {"buy", "evaluate", "pain", "compare", "hire", "research", "other"}
        actual_intent = raw.get("intent", "")
        one_of = exp.get("intent_one_of", list(valid_intents))
        result.assert_check(
            "intent_valid",
            actual_intent in valid_intents,
            f"intent='{actual_intent}' valid={actual_intent in valid_intents}"
        )
        result.assert_check(
            "intent_expected",
            actual_intent in one_of,
            f"intent='{actual_intent}' expected one of {one_of}"
        )

        # ── Assertion 3: confidence within bounds ─────────────────────────
        conf = float(raw.get("confidence", 0.0))
        if "confidence_min" in exp:
            result.assert_check(
                "confidence_min",
                conf >= exp["confidence_min"],
                f"confidence={conf:.2f} min={exp['confidence_min']}"
            )
        if "confidence_max" in exp:
            result.assert_check(
                "confidence_max",
                conf <= exp["confidence_max"],
                f"confidence={conf:.2f} max={exp['confidence_max']}"
            )

        # ── Assertion 4: company_name not null ───────────────────────────
        if exp.get("company_name_notnull"):
            name = raw.get("company_name")
            result.assert_check(
                "company_name_notnull",
                bool(name and name.strip()),
                f"company_name='{name}'"
            )

        # ── Assertion 5: India signals ───────────────────────────────────
        if "india_signals_has" in exp:
            signals = raw.get("india_signals", [])
            found   = [s for s in exp["india_signals_has"] if
                       any(s.lower() in sig.lower() for sig in signals)]
            result.assert_check(
                "india_signals_detected",
                len(found) >= 1,
                f"detected={signals}  needed_one_of={exp['india_signals_has']}"
            )

        # ── Assertion 6: email extracted correctly ───────────────────────
        if "email_extracted" in exp:
            actual_email = (raw.get("email") or "").strip().lower()
            exp_email    = exp["email_extracted"].lower()
            result.assert_check(
                "email_exact",
                actual_email == exp_email,
                f"got='{actual_email}'  expected='{exp_email}'"
            )

        # ── Assertion 7: pain_point not null ─────────────────────────────
        if exp.get("pain_point_notnull"):
            pp = raw.get("pain_point")
            result.assert_check(
                "pain_point_notnull",
                bool(pp and len(pp) > 5),
                f"pain_point='{str(pp)[:60]}'"
            )

        # ── Assertion 8: No hallucinated fields ──────────────────────────
        ALLOWED_KEYS = {
            "company_name", "industry", "location", "company_size",
            "company_domain", "funding_stage", "funding_amount",
            "email", "linkedin_url", "website", "phone", "title",
            "tech_stack", "intent_signals", "confidence", "source",
            "source_url", "is_opportunity", "intent", "urgency",
            "india_signals", "pain_point", "raw_excerpt",
            "tokens_used", "model_used", "analyzed_at",
        }
        extra = set(raw.keys()) - ALLOWED_KEYS
        result.assert_check(
            "no_hallucinated_fields",
            len(extra) == 0,
            f"unexpected keys={extra}" if extra else "clean — no extra fields"
        )

    except ImportError as e:
        result.error = f"ImportError: {e} — check PYTHONPATH includes backend root"
    except Exception as e:
        result.error = f"{type(e).__name__}: {e}"
        result.latency_ms = int((time.monotonic() - t0) * 1000)

    return result


# ── Redis token check ─────────────────────────────────────────────────────────
async def get_token_count() -> int:
    try:
        from backend.llm.cost_guard import get_redis
        r   = await get_redis()
        key = f"gemini:tokens:{date.today().isoformat()}"
        val = await r.get(key)
        return int(val or 0)
    except Exception:
        return -1


# ── Secret scan ───────────────────────────────────────────────────────────────
def scan_secrets() -> list[str]:
    BACKEND = Path(__file__).parents[1] / "backend"
    BAD_PATTERNS = [
        r"AIza[0-9A-Za-z_-]{35}",           # Gemini/GCP key literal
        r"GEMINI_API_KEY\s*=\s*['\"][A-Za-z0-9]",  # hardcoded assignment
        r"sk-[a-zA-Z0-9]{32,}",             # OpenAI-style key
        r"DATABASE_URL\s*=\s*postgres://",  # hardcoded DSN
    ]
    import re
    violations = []
    for py in BACKEND.rglob("*.py"):
        if ".env" in str(py) or "test_" in py.name:
            continue
        text = py.read_text(errors="ignore")
        for pat in BAD_PATTERNS:
            m = re.search(pat, text)
            if m:
                violations.append(f"{py.relative_to(BACKEND.parent)}:{m.group(0)[:30]}")
    return violations


# ── Render ────────────────────────────────────────────────────────────────────
def render(results: list[TestResult], token_count: int, secret_violations: list[str]) -> int:
    ICON = {"PASS": PASS_, "WARN": WARN_, "FAIL": FAIL_}

    print(f"\n{BOLD}{CYAN}{'╔' + '═'*60 + '╗'}{RESET}")
    print(f"{BOLD}{CYAN}║{'LEAD-IQ  ·  DAY 1 EVENING  ·  GEMINI SMOKE TEST':^60}║{RESET}")
    print(f"{BOLD}{CYAN}{'╚' + '═'*60 + '╝'}{RESET}\n")

    passed = 0
    total_tokens_used = 0

    for r in results:
        verdict = r.verdict()
        if verdict == "PASS":
            passed += 1
        icon = ICON[verdict]
        print(f"  {icon}  {BOLD}{r.tc['id']} — {r.tc['label']}{RESET}")
        print(f"       Source: {r.tc['source']}  |  Latency: {r.latency_ms}ms  |  Tokens: {r.tokens_used}")

        if r.error:
            print(f"       {RED}ERROR: {r.error}{RESET}")
        else:
            for name, ok, detail in r.assertions:
                sym = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
                print(f"         {sym}  {name}: {detail}")

        if r.raw_result and verdict != "PASS":
            print(f"       {YELLOW}Raw result (first 300 chars): {json.dumps(r.raw_result)[:300]}{RESET}")
        total_tokens_used += r.tokens_used
        print()

    # ── CHECK 3: Token tracking ───────────────────────────────────────────
    token_ok = token_count > 0
    print(f"  {'✅' if token_ok else '❌'}  CHECK 3 — Redis token tracking")
    print(f"       redis key: gemini:tokens:{date.today().isoformat()}")
    print(f"       value: {token_count if token_count >= 0 else 'REDIS UNAVAILABLE'}")
    if not token_ok:
        print(f"       {YELLOW}FIX: Verify _record_tokens() is called in gemini_service.py{RESET}")
    print()

    # ── CHECK 4: Secrets scan ─────────────────────────────────────────────
    secrets_ok = len(secret_violations) == 0
    print(f"  {'✅' if secrets_ok else '❌'}  CHECK 4 — No secrets committed")
    if secrets_ok:
        print(f"       No API keys or hardcoded credentials found in .py files")
    else:
        for v in secret_violations:
            print(f"       {RED}⚠ VIOLATION: {v}{RESET}")
    print()

    # ── Day 1 Handoff Report ──────────────────────────────────────────────
    est_cost = (token_count if token_count > 0 else total_tokens_used) / 1_000_000 * 0.075
    all_clear = (passed == len(results)) and token_ok and secrets_ok

    print(f"{BOLD}{CYAN}{'─'*62}{RESET}")
    print(f"{BOLD}  ── DAY 1 HANDOFF REPORT ──────────────────────────────────{RESET}")
    print(f"{BOLD}{CYAN}{'─'*62}{RESET}")
    print(f"  Smoke test result  : {GREEN if passed==3 else YELLOW}{passed}/{len(results)} passed{RESET}")
    print(f"  Tokens used today  : {token_count if token_count >= 0 else 'N/A'}")
    print(f"  Est. cost today    : ${est_cost:.4f}  (@ $0.075/M tokens)")
    print(f"  Secrets in code    : {'NONE ✅' if secrets_ok else RED+'FOUND — DO NOT COMMIT'+RESET}")
    print()

    # Failures + unexpected behavior
    failures = [(r.tc["id"], r.error or "assertion failure") for r in results if r.verdict() == "FAIL"]
    if failures:
        print(f"  {RED}{BOLD}Failed cases:{RESET}")
        for tc_id, reason in failures:
            print(f"    {tc_id}: {reason}")
        print()

    # Gemini behavior notes
    print(f"  {BOLD}Gemini behavior notes:{RESET}")
    for r in results:
        if r.raw_result and r.verdict() != "FAIL":
            halluc = set(r.raw_result.keys()) - {
                "company_name","industry","location","company_size","company_domain",
                "funding_stage","funding_amount","email","linkedin_url","website",
                "phone","title","tech_stack","intent_signals","confidence","source",
                "source_url","is_opportunity","intent","urgency","india_signals",
                "pain_point","raw_excerpt","tokens_used","model_used","analyzed_at",
            }
            if halluc:
                print(f"    {YELLOW}⚠ {r.tc['id']}: Hallucinated fields: {halluc}{RESET}")
            else:
                print(f"    ✓ {r.tc['id']}: No hallucinated fields")

    print()
    print(f"  {BOLD}Day 2 priority:{RESET} Wire PostgreSQL DB — see Day 2 execution plan")
    print(f"  {BOLD}Next command:{RESET}")

    if all_clear:
        print(f"""
  {GREEN}git add backend/llm/gemini_service.py backend/api/schemas.py \\
        backend/llm/SOURCE_PROMPTS.py backend/alembic/ \\
        backend/main.py backend/shared/models.py \\
        tests/test_day1_gemini_smoke.py
  git commit -m "feat(day1): wire real Gemini API — engine now fires

  BEFORE: extract_lead() returned mock dicts, no real API calls
  AFTER:  extract_lead() calls gemini-2.0-flash-lite with source prompts

  Changes:
  - Literal intent/urgency type hints in LeadOut (Colvin)
  - Safe json.loads with try/except → return None on failure (Kleppmann)
  - Actual tokens recorded in Redis post-call (Nirav Patel)
  - analyze() returns None on error — never crashes pipeline
  - SELECT 1 DB probe in FastAPI lifespan (Hussein Nasser)
  - engine.dispose() on shutdown
  - india_signals field in schema (default_factory=list)
  - structlog 8 required fields on analysis_complete

  Smoke: {passed}/3 passed | Tokens: {token_count} | Cost: ~${est_cost:.4f}
  Day 2: Wire PostgreSQL DB + first Alembic migration"
  git push origin main{RESET}""")
    else:
        print(f"  {RED}⛔ NOT SAFE TO COMMIT — Fix failures above first{RESET}")

    print(f"\n{BOLD}{CYAN}{'═'*62}{RESET}\n")

    # Return exit code
    if passed == len(results) and token_ok and secrets_ok:
        return 0
    elif passed > 0:
        return 1
    return 2


# ── Entry point ───────────────────────────────────────────────────────────────
async def _main() -> int:
    print(f"\n{CYAN}Running 3 smoke test cases against live Gemini API...{RESET}")

    results = await asyncio.gather(*[run_test_case(tc) for tc in TEST_CASES])
    token_count = await get_token_count()
    secrets     = scan_secrets()

    return render(list(results), token_count, secrets)


def main() -> None:
    code = asyncio.run(_main())
    sys.exit(code)


if __name__ == "__main__":
    main()
