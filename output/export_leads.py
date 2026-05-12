"""
export_leads.py — Collect developer leads from all sources and export to CSV.
"""
import asyncio
import csv
import os
from datetime import UTC, datetime

# ── Collectors ──────────────────────────────────────────────────────────────────
from backend.collectors.hn import HNCollector
from backend.collectors.reddit import RedditCollector
from backend.collectors.stackoverflow import StackOverflowCollector
from backend.collectors.producthunt import ProductHuntCollector

DEV_KEYWORDS = [
    "hiring", "looking for", "build", "developer", "engineer", "tool",
    "startup", "saas", "api", "devops", "cloud", "backend", "frontend",
    "fullstack", "remote", "tech stack", "co-founder", "funding", "series",
    "automation", "microservice", "docker", "kubernetes", "react", "python",
    "aws", "gcp", "azure", "open source", "agent",
]

DEV_SUBREDDITS = [
    "startups", "entrepreneur", "SaaS", "devops", "programming",
    "webdev", "reactjs", "python", "dataengineering", "cloud",
    "aws", "sysadmin",
]


def match_signals(text: str) -> list[str]:
    """Return matched developer keywords from text."""
    text_lower = text.lower()
    return [kw for kw in DEV_KEYWORDS if kw in text_lower]


def truncate(text: str, max_len: int = 200) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


async def collect_all() -> list[dict]:
    """Collect from all sources and return list of flat lead dicts."""
    leads: list[dict] = []

    # ── Hacker News ─────────────────────────────────────────────────────────
    hn = HNCollector()
    hn_posts = await hn.collect()
    for p in hn_posts:
        signals = match_signals(p.title + " " + p.body)
        leads.append({
            "source": p.source,
            "title": p.title,
            "url": p.url,
            "author": p.author,
            "score": p.score,
            "body_truncated": truncate(p.body),
            "collected_at": p.collected_at.isoformat(),
            "matched_signals": "; ".join(signals),
            "source_detail": "",
        })

    # ── Reddit ──────────────────────────────────────────────────────────────
    reddit = RedditCollector(subreddits=DEV_SUBREDDITS)
    reddit_posts = await reddit.collect()
    for p in reddit_posts:
        signals = match_signals(p.title + " " + p.body)
        sub = p.raw_meta.get("subreddit", "")
        leads.append({
            "source": p.source,
            "title": p.title,
            "url": p.url,
            "author": p.author,
            "score": p.score,
            "body_truncated": truncate(p.body),
            "collected_at": p.collected_at.isoformat(),
            "matched_signals": "; ".join(signals),
            "source_detail": f"r/{sub}",
        })

    # ── Stack Overflow ──────────────────────────────────────────────────────
    so = StackOverflowCollector(pages=2)
    so_posts = await so.collect()
    for p in so_posts:
        signals = match_signals(p.title + " " + p.body)
        tags = ", ".join(p.raw_meta.get("tags", []))
        leads.append({
            "source": p.source,
            "title": p.title,
            "url": p.url,
            "author": p.author,
            "score": p.score,
            "body_truncated": truncate(p.body),
            "collected_at": p.collected_at.isoformat(),
            "matched_signals": "; ".join(signals),
            "source_detail": f"tags: {tags}",
        })

    # ── Product Hunt ────────────────────────────────────────────────────────
    ph = ProductHuntCollector()
    ph_posts = await ph.collect()
    for p in ph_posts:
        signals = match_signals(p.title + " " + p.body)
        leads.append({
            "source": p.source,
            "title": p.title,
            "url": p.url,
            "author": p.author,
            "score": p.score,
            "body_truncated": truncate(p.body),
            "collected_at": p.collected_at.isoformat(),
            "matched_signals": "; ".join(signals),
            "source_detail": "",
        })

    return leads


async def main():
    print("Collecting leads from all sources...")
    leads = await collect_all()
    print(f"Total collected: {len(leads)} leads")

    # Sort by score descending
    leads.sort(key=lambda r: r["score"], reverse=True)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    # Write all leads CSV
    all_path = os.path.join(out_dir, f"developer_leads_{timestamp}.csv")
    fieldnames = [
        "source", "source_detail", "title", "url", "author", "score",
        "body_truncated", "matched_signals", "collected_at",
    ]
    with open(all_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

    # Write filtered (dev-signal only) CSV
    filtered = [l for l in leads if l["matched_signals"]]
    sig_path = os.path.join(out_dir, f"developer_leads_signals_{timestamp}.csv")
    with open(sig_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered)

    # Summary
    print(f"\n  All leads:      {all_path}  ({len(leads)} rows)")
    print(f"  Signal leads:   {sig_path}  ({len(filtered)} rows with developer signal matches)")
    print(f"\nSignal keyword breakdown:")
    from collections import Counter
    counter: Counter[str] = Counter()
    for l in leads:
        for kw in l["matched_signals"].split("; "):
            if kw:
                counter[kw] += 1
    for kw, count in counter.most_common(10):
        print(f"  {kw:20s} → {count:3d} leads")


if __name__ == "__main__":
    asyncio.run(main())
