#!/usr/bin/env python3
"""
eval/run_eval.py — Karpathy-style precision measurement for Lead-iq

Measures field-level precision by comparing LLM extraction results against
hand-verified ground truth. Used to drive iterative improvement in prompts
and extraction logic.

Usage:
    python eval/run_eval.py --source=tracxn
    python eval/run_eval.py --quick
    python eval/run_eval.py --all-sources
    python eval/run_eval.py --mock  # Use deterministic mock (no Gemini needed)

 North Star: >75% field precision vs ground truth
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Project root (eval/ is at project root)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Check if Gemini is configured
def _gemini_configured() -> bool:
    return bool(os.getenv("GCP_PROJECT_ID") or os.getenv("GEMINI_API_KEY"))

# Lazy import to avoid loading when not configured
_extract_lead = None

def _get_extract_lead():
    global _extract_lead
    if _extract_lead is None and _gemini_configured():
        from backend.llm.gemini_service import extract_lead
        _extract_lead = extract_lead
    return _extract_lead


def load_ground_truth() -> list[dict[str, Any]]:
    """Load ground truth leads from eval/ground_truth.json"""
    ground_truth_path = PROJECT_ROOT / "eval" / "ground_truth.json"
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_results() -> dict[str, dict[str, Any]]:
    """Load previously cached results from eval/results.json"""
    results_path = PROJECT_ROOT / "eval" / "results.json"
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: dict[str, dict[str, Any]]) -> None:
    """Save results to eval/results.json for caching"""
    results_path = PROJECT_ROOT / "eval" / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def compute_hash(url: str) -> str:
    """Compute cache key hash from URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def calculate_field_precision(
    extracted: dict[str, Any], expected: dict[str, Any]
) -> tuple[float, dict[str, bool]]:
    """
    Calculate field-level precision.

    Returns:
        (precision_score, field_matches) where field_matches shows which fields matched
    """
    if not expected.get("expected"):
        return 1.0, {}

    expected_fields = expected["expected"]
    matches = {}
    total_fields = 0
    correct_fields = 0

    for field, expected_value in expected_fields.items():
        # Skip confidence_min - it's a threshold, not expected value
        if field == "confidence_min":
            continue

        total_fields += 1
        extracted_value = extracted.get(field)

        # Exact match for string/number
        if extracted_value == expected_value:
            matches[field] = True
            correct_fields += 1
        else:
            matches[field] = False

    # For null expected values, extracted should also be null/empty
    for field, expected_value in expected_fields.items():
        if expected_value is None:
            total_fields += 1
            extracted_value = extracted.get(field)
            if extracted_value is None or extracted_value == "":
                matches[field] = True
                correct_fields += 1
            else:
                matches[field] = False

    if total_fields == 0:
        return 1.0, matches

    return correct_fields / total_fields, matches


def aggregate_scores(
    results: list[tuple[str, dict[str, Any], dict[str, Any]]]
) -> dict[str, Any]:
    """Aggregate individual scores into summary statistics"""
    if not results:
        return {
            "overall_precision": 0.0,
            "field_precisions": {},
            "source_precisions": {},
            "total_leads": 0,
        }

    total_score = 0.0
    field_hits: dict[str, int] = {}
    field_total: dict[str, int] = {}
    source_scores: dict[str, list[float]] = {}

    for source, extracted, expected in results:
        score, matches = calculate_field_precision(extracted, expected)
        total_score += score

        # Track source-level
        if source not in source_scores:
            source_scores[source] = []
        source_scores[source].append(score)

        # Track field-level
        for field, matched in matches.items():
            if field not in field_total:
                field_total[field] = 0
                field_hits[field] = 0
            field_total[field] += 1
            if matched:
                field_hits[field] += 1

    # Calculate final metrics
    overall_precision = total_score / len(results) if results else 0.0

    field_precisions = {}
    for field in field_total:
        field_precisions[field] = field_hits[field] / field_total[field]

    source_precisions = {}
    for source, scores in source_scores.items():
        source_precisions[source] = sum(scores) / len(scores)

    return {
        "overall_precision": round(overall_precision, 4),
        "field_precisions": field_precisions,
        "source_precisions": source_precisions,
        "total_leads": len(results),
        "field_total": field_total,
        "field_hits": field_hits,
    }


async def fetch_page_content(url: str, client: httpx.AsyncClient) -> str:
    """Fetch page content via HTTP. Returns markdown-like text or error message."""
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        # Simple HTML-to-text conversion (strip tags)
        import re
        text = re.sub(r'<[^>]+>', ' ', response.text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:50000]  # Truncate to avoid huge payloads
    except Exception as exc:
        return f"Failed to fetch {url}: {exc}"


async def extract_lead_from_url(
    source: str, url: str, client: httpx.AsyncClient, mock_mode: bool = False
) -> dict[str, Any]:
    """
    Extract lead data from URL.

    Strategy:
    1. If mock_mode or no Gemini credentials: return deterministic mock
    2. If Gemini configured: fetch page + call extract_lead()
    3. On extraction failure: return regex fallback mock
    """
    # Priority 1: Mock mode (deterministic for testing without credentials)
    if mock_mode or not _gemini_configured():
        # Return a structured mock that varies by source for realistic testing
        source_mocks: dict[str, dict[str, Any]] = {
            "tracxn": {
                "company_name": "Tracxn Portfolio Company",
                "industry": "SaaS",
                "location": "Bangalore, India",
                "company_size": "11-50",
                "funding_stage": "seed",
                "tech_stack": ["React", "Node.js"],
                "email": None,
            },
            "github_profile": {
                "company_name": "GitHub Organization",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "company_size": "500+",
                "funding_stage": "public",
                "tech_stack": ["Ruby", "Go", "TypeScript"],
                "email": "support@github.com",
            },
            "producthunt": {
                "company_name": "ProductHunt Launch",
                "industry": "Consumer Tech",
                "location": "Remote",
                "company_size": "1-10",
                "funding_stage": "bootstrapped",
                "tech_stack": ["Next.js", "Vercel"],
                "email": None,
            },
            "hacker_news": {
                "company_name": "HN Startup",
                "industry": "Developer Tools",
                "location": "Remote",
                "company_size": "11-50",
                "funding_stage": "seed",
                "tech_stack": ["Rust", "WebAssembly"],
                "email": "jobs@hnstartup.com",
            },
            "yourstory": {
                "company_name": "YourStory Featured",
                "industry": "Fintech",
                "location": "Mumbai, India",
                "company_size": "51-200",
                "funding_stage": "series_a",
                "tech_stack": ["Python", "Django", "AWS"],
                "email": None,
            },
            "dpiit": {
                "company_name": "DPIIT Recognized Startup",
                "industry": "HealthTech",
                "location": "Delhi, India",
                "company_size": "11-50",
                "funding_stage": "seed",
                "tech_stack": ["Flutter", "Firebase"],
                "email": None,
            },
            "mca21": {
                "company_name": "MCA Registered Pvt Ltd",
                "industry": "Manufacturing",
                "location": "Chennai, India",
                "company_size": "201-500",
                "funding_stage": None,
                "tech_stack": [],
                "email": "info@mcareg.com",
            },
            "indimart": {
                "company_name": "IndiaMART Supplier",
                "industry": "B2B Marketplace",
                "location": "Ahmedabad, India",
                "company_size": "11-50",
                "funding_stage": None,
                "tech_stack": ["PHP", "MySQL"],
                "email": None,
            },
        }
        mock = source_mocks.get(source, source_mocks["tracxn"]).copy()
        mock["source"] = source
        mock["source_url"] = url
        mock["confidence"] = 0.40
        return mock

    # Priority 2: Real extraction with Gemini
    extract_fn = _get_extract_lead()
    if extract_fn is None:
        return {"error": "Gemini not configured", "source": source, "source_url": url}

    try:
        content = await fetch_page_content(url, client)
        result = await extract_fn(content, source, url)
        return result
    except Exception as exc:
        return {
            "error": str(exc),
            "source": source,
            "source_url": url,
            "company_name": None,
            "industry": None,
        }


async def run_evaluation(
    source_filter: str | None = None,
    use_cache: bool = False,
    mock_mode: bool = False,
) -> dict[str, Any]:
    """Run evaluation for specified source(s)"""
    ground_truth = load_ground_truth()

    # Filter by source if specified
    if source_filter:
        ground_truth = [g for g in ground_truth if g["source"] == source_filter]

    if not ground_truth:
        return {
            "error": f"No ground truth found for source: {source_filter}",
            "available_sources": list(set(g["source"] for g in load_ground_truth())),
        }

    results: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    cache: dict[str, dict[str, Any]] = {}

    if use_cache:
        cache = load_existing_results()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for entry in ground_truth:
            source = entry["source"]
            url = entry["input_url"]
            expected = entry["expected"]
            gt_id = entry["id"]

            # Check cache (only use cache in mock mode for now)
            cache_key = compute_hash(url)
            if use_cache and cache_key in cache:
                extracted = cache[cache_key]
            else:
                extracted = await extract_lead_from_url(source, url, client, mock_mode=mock_mode)
                if use_cache:
                    cache[cache_key] = extracted

            results.append((source, extracted, entry))

    # Save cache if used
    if use_cache:
        save_results(cache)

    return aggregate_scores(results)


def print_results(results: dict[str, Any]) -> None:
    """Print evaluation results in a readable format"""
    if "error" in results:
        print(f"Error: {results['error']}")
        print(f"Available sources: {', '.join(results.get('available_sources', []))}")
        return

    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Leads Evaluated: {results['total_leads']}")
    print()

    print("Overall Precision: {:.2%}".format(results["overall_precision"]))
    print()

    if results["overall_precision"] >= 0.75:
        print("✅ PASS: Overall precision >= 75% (North Star)")
    else:
        print("❌ FAIL: Overall precision < 75% (Below North Star)")
    print()

    print("Source-level Precision:")
    print("-" * 40)
    for source, precision in sorted(results["source_precisions"].items(), key=lambda x: -x[1]):
        status = "✅" if precision >= 0.70 else "❌"
        print(f"  {status} {source:15} {precision:.2%}")
    print()

    print("Field-level Precision (top 15):")
    print("-" * 40)
    sorted_fields = sorted(
        results["field_precisions"].items(), key=lambda x: -x[1]
    )[:15]
    for field, precision in sorted_fields:
        status = "✅" if precision >= 0.75 else "❌"
        total = results["field_total"].get(field, "?")
        hits = results["field_hits"].get(field, "?")
        print(f"  {status} {field:20} {precision:.2%} ({hits}/{total})")
    print("=" * 70)


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Lead-iq precision evaluation"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Evaluate single source only (e.g., --source=tracxn)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use cached results (skip live scraping)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all sources (default)",
    )
    parser.add_argument(
        "--source-list",
        action="store_true",
        help="List all available sources",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock extraction (no Gemini credentials needed)",
    )

    args = parser.parse_args()

    if args.source_list:
        sources = set(g["source"] for g in load_ground_truth())
        print("Available sources:", ", ".join(sorted(sources)))
        return 0

    # Determine sources to evaluate
    source_filter = args.source if args.source else (None if args.all else None)

    print(f"Evaluating source(s): {source_filter or 'ALL'}")
    print(f"Cache mode: {'enabled' if args.quick else 'disabled'}")
    print(f"mock mode: {'enabled' if args.mock else 'disabled'}")
    print()

    results = asyncio.run(run_evaluation(source_filter, args.quick, mock_mode=args.mock))
    print_results(results)

    # Exit code: 0 if passing, 1 if failing
    if results["overall_precision"] < 0.75:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
