"""hiring_leads.py — Collect hiring/developer leads with upgraded collectors."""
import asyncio, csv, os
from datetime import UTC, datetime
from collections import Counter

from backend.collectors.hn import HNCollector
from backend.collectors.reddit import RedditCollector
from backend.collectors.stackoverflow import StackOverflowCollector
from backend.collectors.producthunt import ProductHuntCollector
from backend.collectors.rss import RSSCollector
from backend.collectors.internshala import InternshalaCollector

HIRING_KEYWORDS = [
    "hiring", "hire", "job opening", "open position", "we are looking for",
    "join our team", "remote", "engineer", "developer", "tech lead",
    "senior engineer", "full stack", "backend", "frontend", "devops",
    "software engineer", "career", "opportunity", "startup hiring",
    "scaling team", "growing team", "technical co-founder",
    "head of engineering", "cto", "co-founder", "series a",
]

def match_signals(text: str) -> list[str]:
    t = text.lower()
    return [kw for kw in HIRING_KEYWORDS if kw in t]


async def main():
    leads: list[dict] = []

    # HN
    print("Collecting Hacker News...")
    for p in await HNCollector().collect():
        signals = match_signals(p.title + " " + p.body)
        leads.append({
            "source": p.source, "source_detail": "",
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    # Reddit
    print("Collecting Reddit...")
    for p in await RedditCollector(
        subreddits=["hiring", "startups", "cscareerquestions", "remotework",
                     "forhire", "devops", "webdev", "SaaS", "programming"]
    ).collect():
        signals = match_signals(p.title + " " + p.body)
        sub = p.raw_meta.get("subreddit", "")
        leads.append({
            "source": p.source, "source_detail": f"r/{sub}",
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    # Stack Overflow
    print("Collecting Stack Overflow...")
    for p in await StackOverflowCollector(pages=1).collect():
        signals = match_signals(p.title + " " + p.body)
        tags = ", ".join(p.raw_meta.get("tags", []))
        leads.append({
            "source": p.source, "source_detail": f"tags: {tags}",
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    # Internshala (was broken, now fixed!)
    print("Collecting Internshala...")
    for p in await InternshalaCollector(max_pages=5).collect():
        signals = match_signals(p.title + " " + p.body)
        loc = p.raw_meta.get("location", "")
        leads.append({
            "source": p.source, "source_detail": loc,
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    # RSS (was missing feedparser, now fixed!)
    print("Collecting RSS...")
    for p in await RSSCollector(max_entries_per_feed=5).collect():
        signals = match_signals(p.title + " " + p.body)
        leads.append({
            "source": p.source, "source_detail": "",
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    # ProductHunt
    print("Collecting ProductHunt...")
    for p in await ProductHuntCollector().collect():
        signals = match_signals(p.title + " " + p.body)
        leads.append({
            "source": p.source, "source_detail": "",
            "title": p.title, "url": p.url, "author": p.author,
            "score": p.score, "body": p.body,
            "matched_signals": "; ".join(signals),
            "collected_at": p.collected_at.isoformat(),
        })

    print(f"\nTotal collected: {len(leads)} leads")
    leads.sort(key=lambda r: r.get("score", 0) or 0, reverse=True)

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.dirname(os.path.abspath(__file__))

    fieldnames = [
        "source", "source_detail", "title", "url", "author", "score",
        "body", "matched_signals", "collected_at",
    ]

    # All leads
    all_path = os.path.join(out_dir, f"hiring_leads_all_{ts}.csv")
    with open(all_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(leads)

    # Hiring-signal only
    hiring = [l for l in leads if l["matched_signals"]]
    sig_path = os.path.join(out_dir, f"hiring_leads_signals_{ts}.csv")
    with open(sig_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(hiring)

    print(f"All leads:     {all_path}  ({len(leads)} rows)")
    print(f"Signal leads:  {sig_path}  ({len(hiring)} hiring-signal rows)\n")

    # Breakdown
    counter: Counter[str] = Counter()
    for l in leads:
        for kw in l["matched_signals"].split("; "):
            if kw:
                counter[kw] += 1
    print("Top hiring signals:")
    for kw, c in counter.most_common(15):
        print(f"  {kw:25s} → {c:3d}")

    print("\nTop 15 hiring leads by score:")
    for l in hiring[:15]:
        src = l["source"]
        sc = l["score"]
        print(f"  [{src:15s} | {sc:4d}] {l['title'][:85]}")
        print(f"         {l['url']}")


if __name__ == "__main__":
    asyncio.run(main())
