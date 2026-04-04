# Lead-iq Specification Documents

## Overview

This directory contains detailed technical specifications for Lead-iq components.

---

## SPEC_GEMINI_LAYER.md

# GCP Vertex AI Gemini Layer Specification

**Version**: 2.0.0  
**Last Updated**: 2026-04-04

## Architecture

```
backend/llm/
├── gemini_service.py    # Main Gemini interface (extract_lead, parse_response)
├── cost_guard.py        # Token budget tracking (Redis-based)
└── SOURCE_PROMPTS.py    # Source-specific extraction templates
```

## Gemini Models Used

| Model | Use Case | Cost | Max Tokens |
|-------|----------|------|------------|
| gemini-2.0-flash-lite | Bulk extraction | $0.075/M | 1M |
| gemini-2.0-flash | Scoring/parsing | $0.10/M | 1M |
| text-embedding-004 | Embeddings | $0.025/M | 768-dim |
| gemini-2.0-flash | Vision | $0.10/M | 1M |

## API Contract

### `extract_lead(markdown: str, source: str, url: str) -> dict`
- Extracts lead data from page content
- Uses SOURCE_PROMPTS[source] for structured extraction
- Returns normalized lead dict with all fields

### `parse_response(response: str) -> dict`
- Parses Gemini response JSON
- Validates against Pydantic schema
- Returns typed Lead dict

### `compute_confidence(lead: dict, source: str) -> float`
- Calculates confidence score based on:
  - Data completeness
  - Source trust level (SOURCE_TRUST)
  - Response consistency

## Cost Guard Contract

```python
def check_budget(tokens_requested: int) -> bool:
    """Check if request fits within daily budget"""
    # Redis key: gemini:tokens:{date.today().isoformat()}
    # Daily limit: 2,000,000 tokens
    # Returns True if within budget, False otherwise
```

## Source Prompts Format

Each source prompt includes:
1. **Extraction instructions** - Fields to extract, vocabulary, gotchas
2. **Output schema** - JSON schema for response validation
3. **Confidence ceiling** - Maximum confidence for this source

## Error Handling

- Token budget exceeded → return empty dict, log warning
- Gemini API error → retry 3x with exponential backoff
- Invalid response format → log, return partial data

---

## SPEC_DEDUP_ENGINE.md

# Deduplication Engine Specification

**Version**: 1.0.0  
**Last Updated**: 2026-04-04

## Architecture

```
backend/services/
├── dedup_service.py     # 3-tier dedup logic
└── postgres/
    └── queries.py       # pgvector queries
```

## 3-Tier Deduplication Strategy

### Tier 1: Exact Match (Fast)
- Email address
- Company name + location
- LinkedIn profile URL

### Tier 2: Fuzzy Match (Medium)
- Company name with typos
- Similar email domains
- Partial URL matches

### Tier 3: Vector Similarity (Slow)
- pgvector embeddings (768-dim)
- Tech stack vectorization
- Industry semantic matching

## Algorithm

```python
def find_duplicate(lead: dict) -> Lead | None:
    """Check if lead exists in database"""
    # Tier 1: Check exact matches (email, company+location)
    # Tier 2: Check fuzzy matches (Levenshtein < 3)
    # Tier 3: Check vector similarity (cosine > 0.85)
    # Return existing lead or None
```

## pgvector Schema

```sql
ALTER TABLE leads ADD COLUMN embedding vector(768);
CREATE INDEX idx_leads_embedding ON leads USING ivfflat (embedding vector_cosine_ops);
```

## Merge Strategy

When duplicate found:
- Update existing lead with new data
- Preserve original confidence if higher
- Log dedup event for audit trail

---

## SPEC_INDIA_ACTORS.md

# India Data Source Actors Specification

**Version**: 1.0.0  
**Last Updated**: 2026-04-04

## Actors

### 1. DPIIT Startup India (Free, Government)
- URL: `https://startupindia.gov.in/`
- Rate: Unlimited (free API)
- Data: Registered startups, incorporation date, founder details
- Integration: `workers/dpiit-actor/`

### 2. Tracxn (Paid, Enterprise)
- URL: `https://tracxn.com/`
- Rate: 100/day (paid tier)
- Data: Company profiles, funding, tech stack, contacts
- Integration: `workers/tracxn-actor/`

### 3. MCA21 (Free, Government)
- URL: `https://www.mca.gov.in/`
- Rate: Limited (captcha-protected)
- Data: Company filings, directors, financials
- Integration: `workers/mca21-actor/`

## Actor Contract

Each actor must implement:

```python
async def collect(url: str) -> list[Lead]:
    """Collect leads from source URL"""
    # 1. Fetch page with Crawlee (stealth mode)
    # 2. Extract markdown with fit_markdown=True
    # 3. Call gemini_service.extract_lead()
    # 4. Compute confidence
    # 5. Check for duplicates
    # 6. Return list of Lead objects
```

## Data Quality Standards

- Minimum confidence: 0.50 for all sources
- Email validity rate: >70% (measured daily)
- Field precision: >75% (measured via eval/)

---

## SPEC_ICP_ENGINE.md

# Ideal Customer Profile (ICP) Engine Specification

**Version**: 1.0.0  
**Last Updated**: 2026-04-04

## Architecture

```
backend/services/
├── icp_service.py       # ICP parsing, matching, scoring
└── models/
    └── icp.py           # ICP SQLAlchemy model
```

## ICP Schema

```python
class ICP(Base):
    id: UUID
    name: str                    # "SaaS Startup Series A"
    description: str             # Natural language description
    target_industries: list[str] # e.g., ["SaaS", "Fintech"]
    min_size: int               # Minimum company size
    max_size: int               # Maximum company size
    min_funding: int            # Minimum funding stage (in $)
    tech_stack: list[str]       # Required/preferred tech
    created_at: datetime
```

## ICP Parser (Gemini Flash)

Input: Natural language ICP description
```
"Target Indian SaaS startups with 11-50 employees, 
Series A funding, using React/Node.js stack"
```

Output: Structured ICP dict
```json
{
  "industries": ["SaaS"],
  "min_size": 11,
  "max_size": 50,
  "min_funding": 5000000,
  "tech_stack": ["React", "Node.js"]
}
```

## Semantic Matching

```python
def match_icp(lead: dict, icp: ICP) -> float:
    """Calculate ICP fit score (0-100)"""
    # 1. Industry match (binary)
    # 2. Company size scoring (linear decay)
    # 3. Tech stack overlap (Jaccard index)
    # 4. Funding threshold scoring
    # 5. Weighted combination
```

## pgvector Integration

- ICP embeddings stored in database
- Lead vector compared against ICP vectors
- Cosine similarity threshold: 0.70

---

## SPEC_DASHBOARD.md

# Analytics Dashboard Specification

**Version**: 1.0.0  
**Last Updated**: 2026-04-04

## North Star Metrics

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| field_precision | >75% | — | eval/run_eval.py |
| email_validity_rate | >70% | — | LeadEvent tracking |
| gemini_tokens_used | <2M/day | — | Redis counters |
| daily_active_users | 10+ | — | Auth tracking |

## Metrics Collection

### Real-time
- Daily token usage (Redis: `gemini:tokens:{date}`)
- API request counts (Redis: `api:requests:{date}`)
- Lead collection count (Redis: `leads:collected:{date}`)

### Batch (Daily)
- Precision scores (eval/run_eval.py --quick)
- Email validity rate (LeadEvent analysis)
- Cost projections (Redis + pricing data)

## Dashboard Endpoints

### GET /api/dashboard/metrics
```json
{
  "today": {
    "tokens_used": 450000,
    "tokens_remaining": 1550000,
    "cost_estimate": "$34.50",
    "leads_collected": 234
  },
  "yesterday": {
    "tokens_used": 380000,
    "precision": 0.78
  }
}
```

### GET /api/dashboard/leading_sources
```json
{
  "sources": [
    {"source": "github_profile", "leads": 120, "precision": 0.82},
    {"source": "tracxn", "leads": 85, "precision": 0.65},
    {"source": "producthunt", "leads": 45, "precision": 0.58}
  ]
}
```

---

## Testing Strategy

All specs tested via:
1. Unit tests (pytest)
2. Integration tests (Playwright)
3. Eval loop (precision measurement)

Run: `python eval/run_eval.py --source=$SOURCE`
