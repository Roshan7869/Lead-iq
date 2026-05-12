# LeadIQ 10-Day Sprint: "Project Starship"
## Build The World's #1 Lead Hunter in 10 Days (Adaptive Imagining Cat Execution)

> **"The best way to predict the future is to create it." — Abraham Lincoln**
>
> **"I think it's possible for ordinary people to be extraordinary." — Elon Musk**

---

## DAY 1-2: PIPELINE FIXATION & SCORING ENGINE MERGE
**Goal: Make the scoring engine actually work in production**

### Phase 1.1: Merge 12-Dim Scorer into Production Pipeline
- **What**: Replace old 3-layer scorer with new 12-dim engine in `workers/analyzer.py`
- **Why**: The 12-dim engine is a masterpiece but currently an orphan
- **How**: 
  1. Import `MultiDimensionalScorer` in analyzer.py
  2. Run 12-dim scoring PERIODICALLY before LLM call (fallback)
  3. Replace heuristic scorer with 12-dim scorer as default
  4. Keep Gemini as opt-in premium
- **Success**: Score 10+ leads, see WARM/HOT outputs, 0 errors

### Phase 1.2: 4-Tier LLM Fallback (WorldMonitor Pattern)
```python
CHAIN: Ollama (local) → Groq (fast) → OpenRouter (cheap) → Browser T5 (last resort)
```n- **Ollama**: phi3:mini (3.8B, 2GB RAM, ~1s per inference)
- **Groq**: llama3.1-8b (8B, ultra-fast, free tier: 500 req/min)
- **OpenRouter**: Multiple models (mixtral-8x7b, free tier generous)
- **Browser T5**: Transformers.js (pure JS, zero server, last resort)
- **Success**: Classification works with NO API keys at all

### Phase 1.3: Scoring Threshold Calibration
```
Target: 5% HOT, 15% WARM, 30% COOL, 50% COLD
Current: 0% HOT, 1% WARM, 4% COOL, 95% COLD
```
- Lower thresholds for uncleared scoring: HOT ≥70, WARM ≥55, COOL ≥40
- Add LLM semantic boost to heuristics (33% weight average)
- Implement cross-source verification bonus
- **Success**: >5% HOT leads from real runs

---

## DAY 3-4: PERSONA RECONNAISSANCE ENGINE (Sherlock Clone)
**Goal: Find lead's social profiles, infer contact, auto-enrich**

### Phase 2.1: Social Profile Discovery
- **Username permutation**: `john` → `john`, `john_doe`, `john.doe`, `johndoe`
- **Platform checks** (async parallel):
  - GitHub: `api.github.com/users/{username}` → bio, company, blog, email
  - Twitter: `nitter.privacydev.net/{username}` (nitter is free, no auth)
  - LinkedIn: Public profile scraper (via Scrapling)
  - HN: `hacker-news.firebaseio.com/v0/user/{username}.json`
  - Dev.to, Medium, IndieHackers, AngelList (public pages)

### Phase 2.2: Contact Inference
- **Email patterns**: `first.last@company.com`, `first@company.com`
- **Domain inference**: Company from bio → guess domain
- **Work history**: Parse job titles from bio + recent activity
- **Tech stack**: Extract from GitHub repos + HN/job posts
- **Persona**: CTO/VP = Decision Maker, Engineer = Influencer, Intern = Unknown

### Phase 2.3: Automatic Enrichment Pipeline
- When scorer detects `pain_explicit` or `hiring_intent`, trigger reconnaissance
- **Parallel**: Check 5-6 social profiles at once
- **Timeout**: 5s per source, fail gracefully
- **Cache**: Redis TTL 24h to avoid re-checking

---

## DAY 5-6: ANTI-DETECTION COLLECTORS (Scrapling Integration)
**Goal: Scrap LinkedIn, AngelList, Crunchbase without being blocked**

### Phase 3.1: Scrapling Wrapper
```python
from scrapling.fetchers import StealthyFetcher

fetcher = StealthyFetcher(headless=True, solve_cloudflare=True)
page = fetcher.fetch("https://www.linkedin.com/company/acme/posts/")
posts = page.css('.feed-shared-update-v2__description').getall()
```

### Phase 3.2: New Anti-Detection Collectors
| Source | Method | Value |
|--------|--------|-------|
| LinkedIn | StealthyFetcher + session cookies | Hiring posts, company updates |
| AngelList | StealthyFetcher | Startups raising, hiring |
| Crunchbase | Public pages + RSS | Funding rounds, acquisitions |
| Company "About" pages | Fetcher + adaptive parsing | Company size, industry, tech |
| Job boards (Indeed, Glassdoor) | Fetcher + HTML parsing | Open roles, salaries |

### Phase 3.3: Proxy Rotation (Built-in)
- Scrapling's `ProxyRotator` with free proxies (Scrapling handles this)
- Per-domain rate limiting
- Fallback to direct if proxy fails

---

## DAY 7-8: MULTI-SOURCE SIGNAL FUSION + TEMPORAL ANOMALIES (WorldMonitor Clone)
**Goal: Cross-reference signals across sources + detect trends before anyone else**

### Phase 4.1: Signal Fusion Engine
```python
Same company mentioned in:
  - HN (today): "We're switching from A to B"                   → tech_signal
  - Reddit (3 days ago): "Hiring 5 engineers for new stack"     → hiring_signal
  - GitHub (1 week ago): "Open issue: evaluate alternatives"    → pain_signal
  → CROSS-CORRELATION CONFIDENCE: 85/100
  → LEAD SCORE BOOST: +20 points
```

### Phase 4.2: Temporal Anomaly Detection (Welford's Algorithm)
```
Baseline (90-day rolling):
  - "Kubernetes" mentions: 5/day average
  - "Kubernetes" mentions this week: 20/day
  - Z-Score: 3.2x above baseline
  → ALERT: "Kubernetes adoption spike detected"
  → Boost any lead mentioning Kubernetes by 15 points
```

### Phase 4.3: Geographic Convergence
```
Cell: San Francisco Bay Area (37.77, -122.41)
  3 events in 24h:
    - StartupCo: hiring React devs (HN)
    - TechCorp: switching to Next.js (Reddit)
    - Innovate Inc: "looking for alternatives to Vercel" (GitHub)
  → GEO CLUSTER: Bay Area Next.js ecosystem momentum
  → Boost all 3 leads by 10 points
```

---

## DAY 9-10: MCP-FIRST + TUI DASHBOARD + PRODUCTION HARDENING
**Goal: Make LeadIQ the platform AI agents reach for first**

### Phase 5.1: MCP Server
```json
{
  "tools": [
    "find_leads_api",
    "enrich_profile", 
    "generate_outreach",
    "track_competitor",
    "get_trending_topics",
    "export_leads_to_csv"
  ]
}
```
- AI agents (Claude, Cursor, VS Code) auto-discover and use LeadIQ
- No manual API integration needed

### Phase 5.2: TUI Dashboard (Go + Bubble Tea)
```
┌──────────────────────────────────────────────┐
│  LeadIQ v3 — WORLDCLASS LEAD HUNTER         │
│  HOT: 12  WARM: 47  COOL: 123  COLD: 892    │
├──────────────────────────────────────────────┤
│  [↑↓] Navigate [Enter] Detail [f] Filter    │
│  [s] Score [t] Trends [e] Export [q] Quit   │
├──────────────────────────────────────────────┤
│  ► 🔥 HOT  StartupCo — Pain signal detected  │
│  │   "Why we left Kubernetes" (score: 88)  │
│  │   Source: HN+GitHub | Persona: CTO       │
│  │   Email: chris@startupco.com (inferred)   │
│  │   Confidence: 92% | Urgency: HIGH        │
├──────────────────────────────────────────────┤
│  ► 🌡 WARM TechCorp — Hiring React Devs      │
│  │   Score: 76/100                          │
│  │   Sources: Reddit, LinkedIn              │
│  │   Persona: VP Engineering (Decision Mkr) │
└──────────────────────────────────────────────┘
```

### Phase 5.3: Production Hardening
- ruff + mypy clean
- pytest ≥80% coverage on new modules
- Docker compose for full stack (API + workers + Ollama + Neo4j + Redis + Postgres)
- GitHub Actions CI passes
- Updated PRODUCTION_READINESS_REPORT.md → 9.0/10

---

## 🗓️ AGGRESSIVE DAILY SCHEDULE

```
Day 1 (Monday):
  06:00-10:00  Merge 12-dim scorer into analyzer.py
  10:00-12:00  4-tier LLM fallback chain (Ollama → Groq → OpenRouter → T5)
  14:00-18:00  Fix scoring thresholds, run benchmarks
  18:00-19:00  Checkpoint: Score 10 leads, see HOT/WARM results
  STATUS: Scoring engine production-ready

Day 2 (Tuesday):
  06:00-10:00  Sherlock-style persona reconnaissance (username finder)
  10:00-12:00  Social profile scrapers (GitHub, HN, Twitter, LinkedIn)
  14:00-18:00  Contact inference + enrichment pipeline
  18:00-19:00  Checkpoint: Enriched leads have email/persona/tech stack
  STATUS: Auto-enrichment live

Day 3 (Wednesday):
  06:00-10:00  Scrapling integration
  10:00-12:00  Anti-detection LinkedIn/AngelList/Crunchbase collectors
  14:00-18:00  Proxy rotation + rate limiting
  18:00-19:00  Checkpoint: New collectors return real data without 403
  STATUS: Anti-detection layer live

Day 4 (Thursday):
  06:00-10:00  Multi-source signal fusion engine
  10:00-12:00  Cross-source correlation scoring (+20 pts for 3+ sources)
  14:00-18:00  Welford's temporal anomaly detection
  18:00-19:00  Checkpoint: Geographic convergence + temporal anomalies detected
  STATUS: Intelligence layer v1 complete

Day 5 (Friday):
  06:00-10:00  MCP Server implementation
  10:00-12:00  MCP tool discovery + registration
  14:00-18:00  TUI Dashboard (Go + Bubble Tea)
  18:00-19:00  Checkpoint: AI agents auto-discover LeadIQ
  STATUS: MCP + TUI live

Day 6-7 (Weekend):
  AGGRESSIVE OPTIMIZATION
  - Score 1000+ leads across all sources
  - Tune thresholds for target distribution
  - Fix any stability issues
  - Performance profiling

Day 8 (Monday):
  06:00-18:00  Production hardening
  - Docker compose full stack
  - ruff + mypy clean
  - pytest coverage ≥80%
  - CI/CD passes

Day 9 (Tuesday):
  06:00-18:00  Benchmark + calibration
  - Run against 500 real leads
  - Compare vs Apollo/ZoomInfo metrics
  - Publish results

Day 10 (Wednesday):
  06:00-12:00  Final fixes + documentation
  12:00-14:00  PRODUCTION_READINESS_REPORT.md → 9.0/10
  14:00-18:00  Celebrate: The world's #1 lead hunter is born
```

---

## 🎯 SUCCESS CRITERIA (Day 10 Must-Haves)

| Metric | Target | How to Verify |
|--------|--------|---------------|
| HOT leads | >5% of total | Run pipeline on 500 leads, count |
| WARM leads | >15% of total | Run pipeline on 500 leads, count |
| Intent accuracy | >70% | Manual ground truth on 50 leads |
| False positive | <30% | Manual ground truth on 50 leads |
| Sources | >15 | List all active collectors |
| Contact inference | >40% | Check enriched fields on 50 leads |
| Persona detection | >50% | Check person field on 50 leads |
| LLM fallback | Works w/o API key | Run with no env vars → still scores |
| MCP tools | >5 registered | List via MCP inspector |
| ruff + mypy | Clean | `ruff check backend/ && mypy backend/` |
| pytest | >80% on new modules | `pytest backend/tests/` |
| CI/CD | Green | GitHub Actions passes |

---

## 🚨 FAILURE MODES & MITIGATIONS

| Risk | Probability | Mitigation |
|------|------------|------------|
| Ollama setup fails on Day 1 | Medium | Fallback to Groq free tier (instant) |
| Sherlock scraping rate-limited | High | Proxy rotation + 5s timeout per request |
| Scraping blocks (Cloudflare) | Medium | Scrapling handles this natively |
| Test coverage <80% on Day 8 | Medium | Write tests in parallel with features |
| Context window overflow | Medium | Checkpoint after each day, compact old context |
| Gemini/outreach API costs | LOW | We're building free alternatives! |