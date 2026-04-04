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
