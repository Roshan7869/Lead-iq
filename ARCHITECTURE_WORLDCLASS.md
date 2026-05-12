# LeadIQ v3 — World Class Architecture
## "Open-Sourced. Unbeatable. Free."

### Philosophy
Build the #1 lead hunter WITHOUT any paid API by:
1. Combining **15+ free data sources** into unified intent signals
2. Using **local open-source LLMs** (no paid inference)
3. Building a **graph intelligence layer** (relationship mapping)
4. Creating a **signal amplification engine** (weak signals → strong leads)

---

## Architecture Layers (L0-L6)

```
┌─────────────────────────────────────────────────────────────────┐
│ L6: ENRICH + AUDIENCE                                          │
│    ├─ Contact inference (email patterns, GitHub, HN profiles)  │
│    ├─ Company registry lookup (OpenCorporates, EDGAR)        │
│    ├─ Batch enrichment (Crunchbase free, LinkedIn public)      │
│    └─ Persona builder (role + intent + tech stack)            │
├─────────────────────────────────────────────────────────────────┤
│ L5: SCORE + PREDICT                                            │
│    ├─ Multi-dimensional scoring (up to 12 signals per lead)    │
│    ├─ Recency decay (freshness weighting)                      │
│    ├─ Implicit vs explicit signals (passive + active)         │
│    └─ Confidence calibration (fake vs real intent)             │
├─────────────────────────────────────────────────────────────────┤
│ L4: INTELLIGENCE LAYER                                         │
│    ├─ Entity extraction (company, person, tech, money)        │
│    ├─ Relationship graph (Neo4j)                              │
│    ├─ Signal correlation (cross-source verification)          │
│    ├─ Intent classification (7-class taxonomy)                   │
│    └─ Topic modeling (tech stack, pain points, market)         │
├─────────────────────────────────────────────────────────────────┤
│ L3: TRANSFORM + DEDUP                                          │
│    ├─ Content normalization (all sources → canonical)          │
│    ├─ Entity resolution (fuzzy matching, 99.8% accuracy)    │
│    ├─ Post deduplication (content_hash + URL + title)         │
│    ├─ Family creation (parent/child companies, same org)    │
│    └─ Clustering (k-means on embeddings)                      │
├─────────────────────────────────────────────────────────────────┤
│ L2: STREAM BUS (Redis)                                          │
│    ├─ Stream: raw_posts                                         │
│    ├─ Stream: normalized_posts                                    │
│    ├─ Stream: scored_leads                                       │
│    ├─ Stream: enriched_leads                                     │
│    └─ Pub/Sub: alerts (hot leads, champion moves, funding)       │
├─────────────────────────────────────────────────────────────────┤
│ L1: COLLECT (15+ Free Sources)                                 │
│    ├─ Social: Reddit*, HN*, Twitter*, Discord (public)         │
│    ├─ Code: GitHub Issues/Discussions/PRs*, StackOverflow*    │
│    ├─ Forums: IndieHackers, ProductHunt, Discourse, Slack (pub) │
│    ├─ Jobs: LinkedIn public*, Indeed*, AngelList*, Glassdoor* │
│    ├─ Firmographic: OpenCorporates*, SEC EDAR*, Gov contracts*│
│    ├─ News: Google News RSS*, TechCrunch*, G2/Capterra*      │
│    └─ Regulated: EU TED*, SAM.gov*, public procurement         │
├─────────────────────────────────────────────────────────────────┤
│ L0: DISCOVERY (Sources with )                                  │
│    ├─ Search indexers (HN, Reddit, GitHub, Twitter)           │
│    ├─ RSS feeds (news, blogs, tech)                             │
│    ├─ Web scrapers (company pages, job boards)                 │
│    ├─ API polling (GitHub, OpenCorporates, SEC)              │
│    └─ MCP triggers (when AI needs leads, it's called)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Makes This #1 in the World

| Dimension | Your v3 | Apollo | ZoomInfo | Why You Win |
|-----------|---------|--------|----------|-------------|
| **Intent Source** | Public forums (pain signals) | Static DB | Intent signals | Earlier signal = earlier deal |
| **Data Freshness** | Real-time (RSS+stream) | Daily/weekly refresh | Weekly | Hot leads minutes old |
| **Cost** | $0 | $500-5k/mo | $1k-10k/mo | Free forever |
| **Workflow** | Auto-pipeline + MCP | Web + API | Web + API | AI-native from day 1 |
| **Signal Power** | Weak→Strong amplification | Single signal | Multi-signal | Deep cross-source signals |
| **Customization** | Full source code | Limited | Limited | You control the engine |
| **Community IQ** | Tech-native (HN, GitHub) | Generic | Generic | Knows the dev buyer |
| **Relationship Graph** | Neo4j (free) | Not included | Not included | ALL relationships visible |

---

## 12 Intent Signal Dimensions (Score each lead 0-100)

| # | Signal Dimension | Detection Method | Weight |
|---|-------------------|------------------|--------|
| 1 | **Pain Explicit** | "issue", "problem", "struggling" in post | 15 |
| 2 | **Hiring Intent** | Job posting, "looking for", "hiring" | 12 |
| 3 | **Tech Stack Growth** | New tool adoption, POC, migration | 15 |
| 4 | **Funding/Runway** | "raised", "Series X", "burn rate" | 18 |
| 5 | **User Growth Pressure** | "scale", "traffic", "growth" | 10 |
| 6 | **Champion Risk** | Key person departures, role changes | 15 |
| 7 | **Budget Signals** | "budget", "spending", "investment" | 12 |
| 8 | **Competitive Indicators** | "vs", "alternatives to", "migrate" | 10 |
| 9 | **Urgency** | "asap", "deadline", "production" | 8 |
| 10 | **Category Momentum** | Multiple companies in same niche | 5 |
| 11 | **Community Sentiment** | Positive/negative sentiment in thread | 5 |
| 12 | **Decision Maker Presence** | CTO, VP, Director involved in discussion | 8 |

---

## Unified Lead Score Formula

```
final_score = Σ(signal_weight × signal_strength × freshness_multiplier)

Where:
  freshness_multiplier = exp(-0.693 × days_ago / 7)
  # = 1.0 at day 0, 0.5 at 7 days, 0.25 at 14 days

classification:
  🔥 HOT:   ≥ 85 intent score + < 7 days old
  🌡 WARM:  ≥ 65 intent score + < 14 days old  
  🟢 COOL:  ≥ 50 intent score
  ❄️ COLD:  <  50 intent score
```

---

## Open Data Sources (Zero Cost, High Value)

| Source | Data Type | Signal Strength | Volume | Rate Limit |
|--------|-----------|----------------|--------|------------|
| **HN Algolia** | Intent, discussion | Very High | Low | 1000/hr |
| **GitHub Issues** | Technical pain | Very High | Med | 5000/hr |
| **GitHub Discussions** | Product eval | High | Med | 5000/hr |
| **Reddit (PRAW)** | Pain, hiring, eval | High | High | 60/min |
| **StackOverflow** | Technical hiring | High | Med | 100/hr |
| **OpenCorporates** | Company registry | Medium | Low | 500/day |
| **SEC EDGAR** | Funding, hires | High | Low | 10/sec |
| **LinkedIn Public** | Job postings, posts | Medium | Medium | Gentle |
| **Indeed API** | Job openings | High | High | 1000/day |
| **AngelList** | Startup hiring | Medium | Low | 50/hr |
| **ProductHunt** | Product launches | Medium | Low | 100/hr |
| **IndieHackers** | Revenue, growth pain | Medium | Low | 60/hr |
| **Twitter/X** | Real-time signals | Medium | High | 300/15min |
| **EU TED** | Procurement | Very High | Med | Free |
| **SAM.gov** | US Gov contracts | Very High | Med | Free |
| **Crunchbase Free** | Funding, founders | Medium | Caps | Limited |

---

## Graph Intelligence (Neo4j)

```
Entities:
  (org:Organization) — name, domain, size, funding, tech_stack
  (person:Person) — name, role, email_pattern, gh_handle
  (post:Post) — title, body, timestamp, source, url
  (tech:Technology) — name, category, popularity

Relationships:
  (person)-[:WORKS_AT]->(org)
  (person)-[:AUTHORED]->(post)
  (org)-[:USES]->(tech)
  (org)-[:COMPETES_WITH]->(org)
  (post)-[:MENTIONS]->(org)
  (post)-[:DISCUSSES]->(tech)
  (org)-[:FUNDED_BY]->(investor)

Queries:
  "Find organizations hiring for tech that recently mentioned scaling"
  MATCH (o:Organization)<-[:WORKS_AT]-(p:Person)-[:AUTHORED]->(post:Post)
  WHERE post.body CONTAINS "hiring" AND post.body CONTAINS "scale"
  RETURN o.name, p.name, post.title, post.url
```

---

## AI Intelligence (Zero Cost via Ollama)

Instead of Gemini ($$$), use **local models**:

```
Intent Classification:   Ollama + llama3.1:latest (8B)
Entity Extraction:         Ollama + mistral:latest (7B)
Summary Generation:        Ollama + phi3:latest (3.8B)
Email Pattern Inference:     spaCy + custom NER (zero inference cost)
Sentiment Scoring:           VADER (rule-based) / Flair (free)
Topic Modeling:              BERTopic + DistilBERT (local)
```

---

## Implementation Priority

| Phase | Deliverable | Impact | Effort |
|-------|-------------|--------|--------|
| 1 | GitHub + HN collectors (already done) + Reddit + StackOverflow | + signals | 3d |
| 2 | Neo4j graph + relationship extraction | Intelligence | 2d |
| 3 | Ollama LLM pipeline (intent, entities, scoring) | Accuracy | 2d |
| 4 | OpenCorporates + EDGAR enrichment (companies, funding) | Depth | 2d |
| 5 | Trend aggregator + signal amplifier | Insight | 2d |
| 6 | MCP endpoint + Claude/Gemini integration | Distribution | 1d |
| 7 | Frontend + API (speed + UX) | Usage | 3d |

**Total: ~ 15 days to world-class**

---

## KPI Targets (vs. Commercial)

| Metric | Your v3 Target | Apollo | ZoomInfo |
|--------|---------------|--------|----------|
| Leads/day | 500 | 2000 | 3000 |
| Email accuracy | ~60% (inferred) | ~90% | ~95% |
| Intent accuracy | 75% (LLM) | ~70% | ~65% |
| Signal latency | < 1 hour | ~24 hours | ~24 hours |
| False positive rate | < 30% | ~40% | ~45% |
| Source diversity | 6+ | 3-4 | 3-4 |
| Cost per lead | $0 | ~$0.50 | ~$1.00 |
