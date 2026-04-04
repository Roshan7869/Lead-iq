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
