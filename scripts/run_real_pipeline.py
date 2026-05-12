"""
run_real_pipeline.py — REAL-source lead pipeline (no imports from backend).
Fetches live data from HN, runs heuristic analysis, outputs scored leads.
Uses: HN Algolia API (free, no auth required)
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    raise SystemExit(1)

SEARCH_QUERIES = [
    "claude hiring",
    "claude job opening",
    "claude code startup",
    "anthropic careers",
    "AI engineer hiring",
    "LLM developer job",
]

HIRING_KEYWORDS = {
    "hiring": 30, "job opening": 25, "join us": 25, "looking for": 15, "opportunities": 10,
    "careers": 12, "apply": 12, "remote": 5, "engineer": 8, "developer": 6,
    "senior": 5, "founding": 15, "founding engineer": 20,
}

CLAUDE_KEYWORDS = {
    "claude": 25, "anthropic": 20, "claude ai": 35, "claude code": 40,
    "claude sonnet": 30, "claude api": 28,
}

PAIN_KEYWORDS = {
    "frustrated": 8, "struggling": 7, "wasted": 6, "slow": 4,
    "difficult": 6, "headache": 7, "annoying": 5, "issue": 3,
}

NEGATIVE_SIGNALS = {
    "spam": -50, "not hiring": -40, "not looking": -30, "not interested": -25,
    "joke": -20, "meme": -15,
}

SALARY_PAT = re.compile(r"[$\u20ac£]\s?\d{1,3}[k]?\s?[-–]\s?[$\u20ac£]?\s?\d{1,3}[k]?", re.IGNORECASE)
COMPANY_PAT = re.compile(r"at\s+([A-Z][A-Za-z0-9\s&]+)\s*(?:\s|$|[`'\"])", re.IGNORECASE)
HREF_PAT = re.compile(r'<a href="(https?://[^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)

def clean_html(text: str) -> str:
    """Strip simple HTML tags."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return text

def score_post(title: str, body: str) -> tuple[int, str, str, str, str | None]:
    text = f"{title} {body}".lower()
    score = 20

    # Keyword scoring
    for kw, w in HIRING_KEYWORDS.items():
        if kw in text:
            score += w
    for kw, w in CLAUDE_KEYWORDS.items():
        if f" {kw} " in f" {text} ":
            score += w
    for kw, w in PAIN_KEYWORDS.items():
        if kw in text:
            score += w
    for kw, w in NEGATIVE_SIGNALS.items():
        if kw in text:
            score += w

    # Intent classification
    is_hiring = any(kw in text for kw in ["hiring", "join us", "job", "opening", "opportunities", "careers"])
    if is_hiring:
        intent = "hiring"
    elif any(kw in text for kw in ["frustrated", "struggling", "issue", "slow"]):
        intent = "pain"
    else:
        intent = "discover"

    # Company extraction
    company_match = COMPANY_PAT.search(title[:100])
    company = (company_match.group(1).strip() if company_match else "Unknown")

    # Score bands
    if score >= 85:
        band = "hot"
    elif score >= 65:
        band = "warm"
    elif score >= 40:
        band = "cool"
    else:
        band = "cold"

    # Salary
    salary_match = SALARY_PAT.search(f"{title} {body}")
    salary = salary_match.group(0) if salary_match else None

    return score, band, intent, company, salary

async def fetch_hn() -> list[dict[str, Any]]:
    print("Fetching real post from HN Algolia API...")
    posts = []
    url = "https://hn.algolia.com/api/v1/search"

    async with httpx.AsyncClient(timeout=20.0) as client:
        for query in SEARCH_QUERIES:
            try:
                resp = await client.get(url, params={
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": 15,
                })
                resp.raise_for_status()
                for hit in resp.json().get("hits", []):
                    title = clean_html(hit.get("title") or "").strip()
                    story = hit.get("story_text") or ""
                    if not title:
                        continue
                    posts.append(unique_post(hit["objectID"], title, story, hit))
            except Exception as exc:
                print(f"  Error fetching '{query}': {exc}")
                continue

    print(f"  Fetched {len(posts)} total posts from HN")
    return posts

def unique_post(object_id: str, title: str, body: str, hit: dict) -> dict[str, Any]:
    created = hit.get("created_at_i")
    from datetime import UTC, datetime
    return {
        "source": "hn",
        "external_id": object_id,
        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
        "title": title,
        "body": clean_html(body),
        "author": hit.get("author", "unknown"),
        "score": hit.get("points") or 0,
        "created_at": (datetime.fromtimestamp(created, tz=UTC).isoformat() if created else None),
    }

async def main():
    print("="*70)
    print("LeadIQ REAL Pipeline — 'claude code jobs'")
    print("="*70)
    print(f"Start: {datetime.now(UTC).isoformat()}")
    print(f"Sources: HN Algolia (real, no auth)")
    print(f"Model: Heuristic (no API key needed)")
    print("-"*70)

    # 1. Collect real data
    raw_posts = await fetch_hn()

    if not raw_posts:
        print("No posts found from HN. Trying GitHub search...")

    # 2. Analyze each post
    leads: list[dict[str, Any]] = []
    for post in raw_posts:
        score, band, intent, company, salary = score_post(post["title"], post["body"])
        if score < 40:  # Filter low-quality
            continue

        leads.append({
            "company_name": company,
            "intent": intent,
            "score": score,
            "score_band": band,
            "confidence": min(score / 100.0, 1.0),
            "title": post["title"],
            "url": post["url"],
            "author": post["author"],
            "salary": salary,
            "source": post["source"],
            "collected_at": post["created_at"],
        })

    # Sort by score desc
    leads.sort(key=lambda x: (-x["score"], x["company_name"]))

    # 3. Output
    print(f"\nFound {len(leads)} leads\n")
    for rank, lead in enumerate(leads, 1):
        print(f"  #{rank}  [{lead['score_band'].upper()}]  {lead['score']}/100  {lead['company_name']}")
        print(f"       Intent: {lead['intent']:<10}  Author: @{lead['author']}")
        print(f"       Title: {lead['title'][:70]}{'...' if len(lead['title']) > 70 else ''}")
        if lead['salary']:
            print(f"       Salary: {lead['salary']}")
        print(f"       URL: {lead['url']}")
        print()

    # Summary
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "query": "claude code jobs",
        "sources": ["hn"],
        "total_posts": len(raw_posts),
        "total_leads": len(leads),
        "bands": {
            "hot": len([l for l in leads if l["score_band"] == "hot"]),
            "warm": len([l for l in leads if l["score_band"] == "warm"]),
            "cool": len([l for l in leads if l["score_band"] == "cool"]),
        },
    }

    print("-"*70)
    print(f"Done: {summary['total_leads']} leads")
    print(f"  Hot: {summary['bands']['hot']} | Warm: {summary['bands']['warm']} | Cool: {summary['bands']['cool']}")
    print("-"*70)
    with open("pipeline_output.json", "w") as f:
        json.dump({"summary": summary, "leads": leads}, f, indent=2)
        print("Results written to pipeline_output.json")

if __name__ == "__main__":
    asyncio.run(main())
