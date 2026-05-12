"""
functional_test_digital_marketing.py — Complete functional test with REAL data.
Searches HN for "digital marketing" leads, runs through full pipeline.
NO synthetic data. All posts are from HN Algolia API.
"""
from __future__ import annotations

import asyncio
import json
import sys
import re
from datetime import UTC, datetime
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install: uv add httpx")
    raise SystemExit(1)

# ── Configuration ──────────────────────────────────────────────────────────
SEARCH_TERMS = [
    "digital marketing",
    "marketing automation",
    "SEO tools",
    "growth hacking",
    "email marketing platform",
    "marketing analytics",
    "social media management",
    "PPC tools",
    "content marketing",
    "lead generation tools",
]

KEYWORD_WEIGHTS = {
    "hiring": 30, "hiring now": 35, "looking for": 15, "seeking": 15,
    "open role": 20, "positions open": 20, "careers": 12, "apply": 12,
    "talent": 10, "engineer": 8, "developer": 6, "remote": 5,
    "digital marketing": 25, "marketing tool": 20, "marketing automation": 22,
    "SEO": 15, "growth hack": 18, "email marketing": 18, "PPC": 12,
    "content marketing": 16, "social media": 14, "lead generation": 16,
    "analytics": 14, "MarTech": 20, "marketing tech": 20, "marketing platform": 18,
}

NEGATIVE = {"spam": -50, "not hiring": -40, "joke": -20, "meme": -15}

SALARY_PAT = re.compile(r"[$€£]\s?\d{1,3}[k]?\s?[-–]\s?[$€£]?\s?\d{1,3}[k]?", re.I)
COMPANY_PAT = re.compile(r"at\s+([A-Z][A-Za-z0-9\s&]+)\s*(?:\s|$|[,.])", re.I)

class Processor:
    """Pipeline processor: fetch → analyze → score → band."""

    @staticmethod
    async def fetch_hn(query: str, per_page: int = 30) -> list[dict[str, Any]]:
        """Fetch real posts from HN Algolia."""
        url = "https://hn.algolia.com/api/v1/search"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url, params={
                    "query": query,
                    "tags": "story",
                    "hitsPerPage": per_page,
                })
                resp.raise_for_status()
                return [
                    {
                        "source": "hn",
                        "external_id": hit["objectID"],
                        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                        "title": hit.get("title", "").strip(),
                        "body": hit.get("story_text", "") or "",
                        "author": hit.get("author", "unknown"),
                        "score": hit.get("points", 0) or 0,
                        "created_at": datetime.fromtimestamp(hit.get("created_at_i", 0), tz=UTC).isoformat() if hit.get("created_at_i") else None,
                    }
                    for hit in resp.json().get("hits", [])
                ]
        except Exception:
            return []

    @staticmethod
    def analyze(post: dict[str, Any]) -> dict[str, Any]:
        """Heuristic analysis — real scoring."""
        text = f"{post['title']} {post['body']}".lower()
        score = 20

        for kw, w in KEYWORD_WEIGHTS.items():
            if kw.lower() in text:
                score += w
        for kw, w in NEGATIVE.items():
            if kw in text:
                score += w

        is_hiring = any(k in text for k in ["hiring", "join us", "looking for", "open role", "opportunities", "careers"])
        is_digital_marketing = any(kw in text for kw in ["digital marketing", "marketing tool", "marketing automation", "marketing tech", "martech", "SEO", "email marketing"])

        intent = "hiring" if is_hiring else "evaluate" if any(k in text for k in ["looking for", "recommend", "alternatives to"]) else "discover"
        if is_digital_marketing:
            score += 25

        band = "hot" if score >= 85 else "warm" if score >= 65 else "cool" if score >= 40 else "cold"
        company_match = COMPANY_PAT.search(post["title"])
        company = company_match.group(1).strip() if company_match else "Unknown"
        salary = SALARY_PAT.search(f"{post['title']} {post['body']}")

        return {
            "company": company,
            "title": post["title"],
            "url": post["url"],
            "author": post["author"],
            "score": min(score, 150),
            "score_band": band,
            "intent": intent,
            "confidence": min(score / 150.0, 1.0),
            "salary": salary.group(0) if salary else None,
            "source": "hn",
            "created_at": post.get("created_at"),
        }


async def main():
    print("=" * 80)
    print("LeadIQ Functional Test — Digital Marketing Tech Leads")
    print("=" * 80)
    print(f"Start: {datetime.now(UTC).isoformat()}")
    print("Note: All posts are REAL data from HN Algolia API. No synthetic data.")
    print("-" * 80)

    posts = []
    for term in SEARCH_TERMS:
        results = await Processor.fetch_hn(term)
        print(f"  '{term}': {len(results)} posts")
        posts.extend(results)

    print(f"\nTotal raw posts: {len(posts)}\n")

    seen = set()
    leads = []
    for post in posts:
        if post["url"] in seen:
            continue
        seen.add(post["url"])
        lead = Processor.analyze(post)
        if lead["score"] >= 40:  # Filter low-quality
            leads.append(lead)

    leads.sort(key=lambda x: (-x["score"], x["company"]))

    hot = [l for l in leads if l["score_band"] == "hot"]
    warm = [l for l in leads if l["score_band"] == "warm"]
    cool = [l for l in leads if l["score_band"] == "cool"]

    print(f"\n{'=' * 80}")
    print(f"RESULTS: {len(leads)} qualified leads from {len(posts)} real posts")
    print(f"  Hot:  {len(hot)} | Warm: {len(warm)} | Cool: {len(cool)}")
    print(f"{'=' * 80}\n")

    for rank, lead in enumerate(leads, 1):
        print(f"  #{rank}  [{lead['score_band'].upper()}]  {lead['score']}/150  {lead['company']}")
        print(f"         Intent: {lead['intent']:<10}  Author: @{lead['author']}")
        print(f"         Title: {lead['title'][:70]}{'...' if len(lead['title']) > 70 else ''}")
        if lead['salary']:
            print(f"         Salary: {lead['salary']}")
        print(f"         URL: {lead['url']}")
        print()

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "search_terms": SEARCH_TERMS,
        "total_posts": len(posts),
        "total_leads": len(leads),
        "hot_leads": hot,
        "warm_leads": warm,
        "cool_leads": cool,
    }

    print(f"{'=' * 80}")
    print(f"Functional test complete: {len(leads)} leads generated")
    print(f"{'=' * 80}")
    print(json.dumps({"summary": {k: v for k, v in summary.items() if k not in ("hot_leads", "warm_leads", "cool_leads")}, "leads": leads}, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
