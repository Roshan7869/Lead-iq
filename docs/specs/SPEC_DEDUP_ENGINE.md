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
