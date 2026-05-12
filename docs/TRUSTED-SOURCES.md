# LeadIQ Trusted Data Sources & URL Validation Guide
## Deep-Dive Research: Components, Strategy & Implementation

---

## 1. Government Sources (India)

| Source | URL | Type | Validation Method | Scraping Method |
|--------|-----|------|-------------------|-----------------|
| Startup India | `startupindia.gov.in` | Static | SSL + WHOIS + Gov domain | Static HTML |
| MSME India | `msme.gov.in` | Static | SSL + Gov domain | Static HTML |
| SIDBI | `sidbi.in` | Static | SSL + WHOIS | Static HTML |
| Invest India | `investindia.gov.in` | Static | Gov domain | Static HTML |
| Startup India Schemes | `startupindia.gov.in/content/sid...` | Static | Gov domain | Static HTML |

### Validation Protocol:
```
1. DNS Resolution: Resolve domain → get IP
2. SSL/TLS Check: Verify certificate chain (domain, expiry, issuer)
3. Gov Domain: Check `.gov.in` or `.in` TLD
4. WHOIS Lookup: Verify domain registration > 1 year old
5. Content Hash: SHA-256 of page content for integrity
6. Updated Freshness: Check `Last-Modified` or `sitemap.xml`
7. Robot Policy: Respect `robots.txt` + crawl-delay
```

---

## 2. Job Platforms

| Source | URL | API Available | Auth Required | Rate Limit |
|--------|-----|---------------|---------------|------------|
| LinkedIn (Jobs) | `linkedin.com/jobs` | Yes (Talent Solutions) | OAuth 2.0 | 500/day |
| Indeed | `indeed.com` | Yes (RapidAPI) | API Key | 1000/month |
| Wellfound (AngelList) | `wellfound.com` | Yes | OAuth 2.0 | 500/hour |
| Hacker News "Who's Hiring" | `news.ycombinator.com` | No (HTML) | None | Politeness |
| Reddit r/forhire | `reddit.com/r/forhire` | No | None | 30/min |
| Startup.jobs | `startup.jobs` | Yes | OAuth | 100/hour |
| Otta | `otta.com` | Yes | API Key | 1000/month |

### Scraping Strategy:
```python
# Extract hiring signals from free sources (no API required)
SOURCES = {
    'hn_whois_hiring': 'https://news.ycombinator.com/submitted?id=whoishiring',
    'reddit_forhire': 'https://www.reddit.com/r/forhire/search/?q=hiring&restrict_sr=1&sort=new',
    'indiehackers': 'https://www.indiehackers.com/startups/hiring',
    'devto_jobs': 'https://dev.to/ listings?listing_type=job',
}

# Validation: Check URL domain + SSL + age
```

---

## 3. Startup Funding & News

| Source | URL | Type | Trust Score | Method |
|--------|-----|------|-------------|--------|
| Crunchbase | `crunchbase.com` | API | High (9/10) | API + Web |
| PitchBook | `pitchbook.com` | API | High (9/10) | API |
| TechCrunch | `techcrunch.com` | RSS/News | Medium (7/10) | RSS + Web |
| ProductHunt | `producthunt.com` | API | High (8/10) | API |
| AngelList (Wellfound) | `wellfound.com` | API | High (8/10) | API |
| Inc42 | `inc42.com` | RSS/News | Medium (7/10) | RSS |
| Entrackr | `entrackr.com` | News | Medium (7/10) | RSS |
| Y Combinator | `ycombinator.com/companies` | API | High (9/10) | API |
| Sequoia Surge | `surge.sequoiacap.com` | API | High (9/10) | API |
| Accel Atoms | `atoms.accel.com` | API | High (9/10) | API |

### Trust Validation Protocol:
```
Step 1: Domain Verification
- Check SSL certificate (valid, not expired, issued by trusted CA)
- Confirm domain age (WHOIS lookup > 1 year)
- Verify no DNS issues (no spoofing)

Step 2: Content Verification
- Cross-reference funding claims with 2+ sources
- Check for `ClaimReview` structured data (Google Fact Check)
- Validate against SEC filings (US companies)
- For Indian companies: Check MCA (Ministry of Corporate Affairs)

Step 3: Metadata Extraction
- Extract `publishedAt`, `author`, `publisher` from article
- Check `dateModified` vs `datePublished`
- Verify author credibility (LinkedIn profile, Twitter)

Step 4: Confidence Scoring
- High: Official source (company website, SEC filing, press release)
- Medium: Reputable news (TechCrunch, Bloomberg, Reuters)
- Low: Blog, forum, unverified claim
```

---

## 4. Events & Conferences

| Source | URL | Type | Scraping |
|--------|-----|------|----------|
| TechCrunch Disrupt | `techcrunch.com/events/` | Static | Static |
| Web Summit | `websummit.com` | Static | Static |
| SaaStr Annual | `saastr.com` | Static | Static |
| National Startup Day | `startupindia.gov.in` | Static | Static |
| Startup India Hub | `startupindia.gov.in` | API | JSON API |
| Meetup.com | `meetup.com` | API | Event API |
| Luma (India) | `lu.ma` | API | API |
| Eventbrite | `eventbrite.com` | API | API |

### Scrape Strategy:
```
1. Calendar Integration (iCal/vCal)
2. Event Schema (Schema.org/Event)
3. Google Calendar API for public events
4. LinkedIn Events API
```

---

## 5. Frontend Validation Components

### URL Validator Module
```python
# backend/services/url_validator.py
import validators
import ssl
import socket
import whois
from urllib.parse import urlparse

class URLTrustScorer:
    """Scrape URL trustworthiness with multi-check."""
    
    def __init__(self, url: str):
        self.url = url
        self.domain = urlparse(url).netloc
        self.score = 0
        self.checks = {}
    
    def validate_ssl(self) -> bool:
        """Verify SSL/TLS certificate."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    self.checks['ssl_valid'] = True
                    self.checks['ssl_expiry'] = cert['notAfter']
                    self.score += 2
                    return True
        except Exception as exc:
            self.checks['ssl_valid'] = False
            self.checks['ssl_error'] = str(exc)
            return False
    
    def validate_domain_age(self) -> bool:
        """Check domain registration age."""
        try:
            info = whois.whois(self.domain)
            creation = info.creation_date[0] if isinstance(info.creation_date, list) else info.creation_date
            # Domain registered for at least 1 year = trustworthy
            from datetime import datetime, timedelta
            if (datetime.now() - creation).days > 365:
                self.checks['domain_age'] = 'over_1_year'
                self.score += 2
                return True
            else:
                self.checks['domain_age'] = 'under_1_year'
                return False
        except:
            self.checks['domain_age'] = 'unknown'
            return False
    
    def validate_gov_domain(self) -> bool:
        """Check if it's a government domain."""
        if '.gov.in' in self.domain or '.gov' in self.domain:
            self.checks['gov_domain'] = True
            self.score += 5
            return True
        return False
    
    def validate_url(self) -> dict:
        """Run all checks."""
        self.validate_ssl()
        self.validate_domain_age()
        self.validate_gov_domain()
        
        # Base URL validation
        if not validators.url(self.url):
            self.checks['url_valid'] = False
            return self.checks
        
        self.checks['url_valid'] = True
        self.score += 1
        self.checks['final_score'] = self.score
        self.checks['trust_level'] = self._get_trust_level()
        return self.checks
    
    def _get_trust_level(self):
        if self.score >= 8: return 'high'
        if self.score >= 5: return 'medium'
        return 'low'
```

### Frontend URL Display Component
```tsx
// src/components/UrlTrustBadge.tsx
interface TrustBadgeProps {
  url: string;
  trustScore: number;
}

export function UrlTrustBadge({ url, trustScore }: TrustBadgeProps) {
  const getColor = () => {
    if (trustScore >= 8) return 'bg-green-500';
    if (trustScore >= 5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className={`inline-flex items-center gap-2 px-2 py-1 rounded ${getColor()}`}>
      <span className="text-white text-xs font-mono">
        {trustScore >= 8 ? 'Trusted' : trustScore >= 5 ? 'Verify' : 'Caution'}
      </span>
      <a href={url} target="_blank" rel="noopener noreferrer" className="underline text-xs">
        {new URL(url).hostname}
      </a>
    </div>
  );
}
```

---

## 6. Research Paper Mapping

| Area | Paper | Authors | Year | Relevance |
|------|-------|---------|------|-----------|
| NER | "BERT: Pre-training of Deep Bidirectional Transformers" | Devlin et al. | 2019 | Entity extraction |
| Sentiment | "RoBERTa: A Robustly Optimized BERT Pretraining Approach" | Liu et al. | 2019 | Sentiment scoring |
| Scoring | "XGBoost: A Scalable Tree Boosting System" | Chen & Guestrin | 2016 | Lead scoring |
| Metrics | "XAI Metrics" | Samek et al. | 2020 | Explainability (SHAP) |
| Topic Modeling | "BERTopic: Neural topic modeling" | Grootendorst | 2022 | Topic modeling |
| Event Extraction | "Event Extraction via Dynamic Multi-Pooling CNNs" | Chen et al. | 2015 | Event detection |
| CLV | "Counting Your Customers: The Easy Way" | Fader & Hardie | 2009 | CLV prediction |
| Graph Neural Networks | "Graph Convolutional Networks" | Kipf & Welling | 2017 | Network effects |
| Stream Processing | "Kafka: A Distributed Messaging System" | Kreps et al. | 2011 | Event streaming |
| MCDM | "The Analytic Hierarchy Process" | Saaty | 1980 | Lead ranking |

---

*Validation Protocol Complete — 6 Source Categories, 30+ Trusted Sources*
