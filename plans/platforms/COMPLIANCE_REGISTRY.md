# Compliance Registry (Extended)
> Terms of Service compliance for all 29 platforms
> Risk levels, scraping policies, API availability
> Date: 2026-05-11

---

## COMPLIANCE MATRIX

### Job Platforms

| Platform | Risk Level | ToS URL | Scraping | API | Rate Limit | Retention | Notes |
|----------|-----------|---------|----------|-----|------------|-----------|-------|
| **Naukri.com** | MEDIUM | naukri.com/terms | Allowed | No | 2-4s delays | 30 days | Akamai protection. Use stealth + proxies |
| **Internshala** | LOW | internshala.com/terms | Allowed | No | 2-4s delays | 30 days | No anti-bot. Direct parsing okay |
| **LinkedIn Jobs** | HIGH | linkedin.com/legal | Restricted | Yes | API limits | 7 days | Must use official API. No scraping |
| **Indeed India** | LOW | indeed.com/intl/en/legal | Allowed | Yes | RSS: none | 30 days | RSS feeds designed for aggregation |
| **Shine.com** | MEDIUM | shine.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **Monster India** | MEDIUM | monsterindia.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **Freshersworld** | LOW | freshersworld.com/terms | Allowed | No | Minimal | 30 days | No protection |
| **Hirist** | MEDIUM | hirist.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **CutShort** | MEDIUM | cutshort.io/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **AngelList** | MEDIUM | wellfound.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **Instahyre** | MEDIUM | instahyre.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **IIM Jobs** | MEDIUM | iimjobs.com/terms | Allowed | No | 2-3s delays | 30 days | Standard scraping |
| **NaukriGulf** | MEDIUM | naukrigulf.com/terms | Allowed | No | 2-4s delays | 30 days | Similar to Naukri |
| **Sarkari Result** | LOW | sarkariresult.com | Allowed | No | Minimal | 30 days | Public information |
| **FreeJobAlert** | LOW | freejobalert.com | Allowed | No | Minimal | 30 days | Public information |
| **Employment News** | LOW | employmentnews.gov.in | Allowed | Yes | RSS limits | 90 days | Official government |

### Government Sources

| Platform | Risk Level | ToS URL | Scraping | API | Rate Limit | Retention | Notes |
|----------|-----------|---------|----------|-----|------------|-----------|-------|
| **DPIIT** | LOW | startupindia.gov.in | Allowed | Yes | Unlimited | 90 days | Official public API |
| **MCA21** | LOW | mca.gov.in | Allowed | Yes | Limited | 90 days | Public corporate data |
| **GeM Portal** | LOW | gem.gov.in | Allowed | Yes | Unlimited | 90 days | Official vendor directory |
| **MSME Udyam** | LOW | udyamregistration.gov.in | Allowed | Yes | API Setu | 90 days | Official MSME registry |
| **API Setu** | LOW | apisetu.gov.in | Allowed | Yes | 6Cr/month | 90 days | Official API gateway |

### Social/Existing Sources

| Platform | Risk Level | ToS URL | Scraping | API | Rate Limit | Retention | Notes |
|----------|-----------|---------|----------|-----|------------|-----------|-------|
| **Reddit** | MEDIUM | redditinc.com/policies | Allowed | Yes | 100-600/min | 30 days | OAuth required |
| **HackerNews** | LOW | ycombinator.com/legal | Allowed | Yes | <100/min | 90 days | Public data |
| **GitHub** | LOW | github.com/terms | Allowed | Yes | 5000/hr | 90 days | API preferred |
| **StackOverflow** | LOW | stackoverflow.com/legal | Allowed | Yes | 300/day | 90 days | CC-BY-SA |
| **Twitter/X** | HIGH | twitter.com/en/tos | Blocked | Yes | 500/month | 7 days | API only, expensive |
| **Telegram** | MEDIUM | telegram.org/tos | Allowed | Yes | 30 msg/sec | 30 days | Bot API |
| **ProductHunt** | MEDIUM | producthunt.com/legal | Allowed | Yes | 300/min | 60 days | GraphQL API |
| **RSS** | LOW | N/A | Allowed | N/A | N/A | 90 days | Designed for consumption |

---

## BLOCKED SOURCES

These sources are **explicitly prohibited** from scraping:

| Source | Reason | Alternative |
|--------|--------|-------------|
| Twitter/X web | ToS prohibits scraping | Use official API (expensive) |
| LinkedIn profiles | ToS prohibits scraping | Use Jobs API (with application) |
| Facebook | ToS prohibits scraping | Not applicable |
| Glassdoor | Aggressive anti-bot + legal | Not recommended |

---

## SCRAPING POLICY

### Allowed Practices
✅ Respect robots.txt  
✅ Use official APIs when available  
✅ Rate limiting (max 1 request per 2 seconds)  
✅ Extract only public data  
✅ No personal/private data  
✅ No authentication bypass  
✅ Transparent user agents  
✅ Handle 429/503 gracefully  

### Prohibited Practices
❌ Credential stuffing  
❌ Session hijacking  
❌ CAPTCHA bypass (automated)  
❌ Scraping behind login walls  
❌ Distributed denial of service  
❌ Reselling scraped data  
❌ Automated account creation  
❌ Reverse engineering API keys  

---

## DATA RETENTION POLICY

```python
RETENTION_POLICY = {
    # Job platform data
    "naukri": 30,           # 30 days
    "internshala": 30,      # 30 days
    "linkedin": 7,          # 7 days (high risk)
    "indeed": 30,           # 30 days
    "shine": 30,            # 30 days
    "monster": 30,          # 30 days
    "freshersworld": 30,    # 30 days
    "hirist": 30,           # 30 days
    "cutshort": 30,         # 30 days
    "angellist": 30,        # 30 days
    "instahyre": 30,        # 30 days
    "iimjobs": 30,          # 30 days
    "naukrigulf": 30,       # 30 days
    
    # Government data
    "dpiit": 90,            # 90 days
    "mca21": 90,            # 90 days
    "gem": 90,              # 90 days
    "msme": 90,             # 90 days
    "sarkari_result": 30,   # 30 days
    "freejobalert": 30,     # 30 days
    "employment_news": 90,  # 90 days
    
    # Social data
    "reddit": 30,           # 30 days
    "hn": 90,               # 90 days
    "github": 90,           # 90 days
    "stackoverflow": 90,    # 90 days
    "twitter": 7,           # 7 days (high risk)
    "telegram": 30,         # 30 days
    "producthunt": 60,      # 60 days
    "rss": 90,              # 90 days
}
```

---

## AUDIT TRAIL

### Logging Requirements

All scraping activities must log:
```python
SCRAPE_LOG_SCHEMA = {
    "timestamp": "ISO8601",
    "source": "platform_name",
    "action": "collect|error|rate_limited",
    "url": "scraped_url",
    "status_code": "HTTP status",
    "items_extracted": "count",
    "latency_ms": "response_time",
    "proxy_used": "proxy_ip",
    "user_agent": "ua_string",
    "error": "error_message_if_any",
    "retry_count": "number_of_retries",
}
```

### Audit Schedule

| Audit Type | Frequency | Responsible | Deliverable |
|------------|-----------|-------------|-------------|
| ToS compliance | Weekly | Legal/Compliance | Compliance report |
| Data retention | Monthly | Data team | Retention audit |
| Source health | Daily | Engineering | Health dashboard |
| Privacy review | Quarterly | Privacy officer | Privacy impact |
| Security scan | Monthly | Security team | Vulnerability report |

---

## INCIDENT RESPONSE

### Detection
```
Alert triggers:
- Source returns 403 Forbidden
- Source returns "Access Denied" page
- IP address blocked
- CAPTCHA challenge presented
- Rate limit exceeded (429)
- ToS violation notice received
```

### Response Flow
```
1. DETECT (automatic monitoring)
   └── Alert fired
       
2. ASSESS (within 1 hour)
   └── Determine severity
       ├── LOW: Single request blocked
       ├── MEDIUM: Source temporarily unavailable
       └── HIGH: Legal notice received
       
3. RESPOND (within 4 hours)
   └── Based on severity:
       ├── LOW: Adjust rate limiting, retry
       ├── MEDIUM: Pause source, investigate
       └── HIGH: Stop all scraping, legal review
       
4. RECOVER (within 24 hours)
   └── Resume with adjustments:
       ├── Change proxy IP
       ├── Adjust delay settings
       ├── Switch to official API
       └── Update compliance registry
       
5. DOCUMENT (within 48 hours)
   └── Update:
       ├── Incident log
       ├── Compliance registry
       └── Runbook
```

---

*Compliance Registry*
*Total Platforms: 29*
*Low Risk: 15 | Medium Risk: 11 | High Risk: 3*
*Last Updated: 2026-05-11*
