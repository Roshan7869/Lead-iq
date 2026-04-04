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
