# Complete Platform Catalog
> All job platforms, government sources, and social channels
> URLs, volumes, protection levels, and scraping approaches
> Date: 2026-05-11

---

## TIER 1: CRITICAL (Must Have)

### 1. Naukri.com
- **URL:** https://www.naukri.com/
- **Type:** Job Portal
- **Volume:** 50,000+ jobs/day
- **Protection:** HIGH (Akamai bot protection)
- **Approach:** API interception + Playwright stealth + residential proxies
- **API Endpoint:** `https://www.naukri.com/jobapi/v3/search`
- **Fields:** Title, company, salary, experience, location, skills, work mode
- **Rate Limit:** 2-4 second delays, rotate proxy every 20 requests
- **Compliance Risk:** MEDIUM - requires careful rate limiting
- **Implementation:** Phase 2 (Week 2)

### 2. Internshala
- **URL:** https://internshala.com/
- **Type:** Internship Platform
- **Volume:** 10,000+ internships/day
- **Protection:** MEDIUM
- **Approach:** Direct HTML parsing with stealth headers
- **Pagination:** `/internships/{category}/page-{n}/`
- **Fields:** Title, company, stipend, duration, location, skills
- **Rate Limit:** 2-4 second delays
- **Compliance Risk:** LOW
- **Implementation:** Phase 2-3 (Week 2-3)

### 3. LinkedIn India Jobs
- **URL:** https://www.linkedin.com/jobs/
- **Type:** Professional Network Jobs
- **Volume:** 20,000+ jobs/day
- **Protection:** HIGH
- **Approach:** Official API + stealth browser fallback
- **API:** LinkedIn Jobs API (requires application)
- **Fields:** Title, company, description, skills, experience, location
- **Rate Limit:** Strict - use API when possible
- **Compliance Risk:** HIGH - must use official API
- **Implementation:** Phase 5 (Week 5)

---

## TIER 2: HIGH VALUE

### 4. Indeed India
- **URL:** https://www.indeed.co.in/
- **Type:** Job Aggregator
- **Volume:** 15,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** RSS feeds + API fallback
- **RSS:** `https://www.indeed.co.in/rss?q={keyword}&l={location}`
- **Fields:** Title, company, location, description
- **Rate Limit:** Standard RSS limits
- **Compliance Risk:** LOW - RSS designed for aggregation
- **Implementation:** Phase 5 (Week 5)

### 5. Shine.com
- **URL:** https://www.shine.com/
- **Type:** Job Portal
- **Volume:** 5,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, salary, experience, location
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 6. Monster India
- **URL:** https://www.monsterindia.com/
- **Type:** Job Portal
- **Volume:** 3,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, salary, experience, location
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 7. NaukriGulf
- **URL:** https://www.naukrigulf.com/
- **Type:** Gulf Jobs Portal
- **Volume:** 2,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** API interception (similar to Naukri)
- **Fields:** Title, company, salary, experience, location
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

---

## TIER 3: NICHE/SPECIALIZED

### 8. Freshersworld
- **URL:** https://www.freshersworld.com/
- **Type:** Freshers Job Portal
- **Volume:** 2,000+ jobs/day
- **Protection:** LOW
- **Approach:** Direct parsing
- **Fields:** Title, company, location, qualification
- **Rate Limit:** Minimal
- **Compliance Risk:** LOW
- **Implementation:** Phase 5 (Week 5)

### 9. Hirist
- **URL:** https://www.hirist.com/
- **Type:** Tech Jobs
- **Volume:** 2,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, tech stack, experience, location
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 10. CutShort
- **URL:** https://cutshort.io/
- **Type:** Tech/Startup Jobs
- **Volume:** 1,500+ jobs/day
- **Protection:** MEDIUM
- **Approach:** API + stealth
- **Fields:** Title, company, tech stack, experience, salary
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 11. AngelList India (Wellfound)
- **URL:** https://wellfound.com/
- **Type:** Startup Jobs
- **Volume:** 1,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, equity, salary, stage
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 12. Instahyre
- **URL:** https://www.instahyre.com/
- **Type:** Premium Jobs
- **Volume:** 1,000+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, salary, experience, location
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

### 13. IIM Jobs
- **URL:** https://www.iimjobs.com/
- **Type:** Management Jobs
- **Volume:** 500+ jobs/day
- **Protection:** MEDIUM
- **Approach:** Direct scraping
- **Fields:** Title, company, salary, experience, location
- **Rate Limit:** 2-3 second delays
- **Compliance Risk:** MEDIUM
- **Implementation:** Phase 5 (Week 5)

---

## TIER 4: GOVERNMENT SOURCES

### 14. DPIIT Startup India
- **URL:** https://startupindia.gov.in/
- **API:** https://api.startupindia.gov.in/sih/api/startup/search
- **Type:** Government Startup Registry
- **Volume:** 500+ startups/day (new registrations)
- **Protection:** LOW (official API)
- **Approach:** Official API
- **Fields:** Name, sector, stage, location, founders, funding, CIN, GST
- **Rate Limit:** Unlimited (free public API)
- **Compliance Risk:** LOW
- **Confidence:** 0.85
- **Implementation:** Phase 4 (Week 4)

### 15. MCA21
- **URL:** https://www.mca.gov.in/
- **Type:** Corporate Registry
- **Volume:** 800+ companies/day (new registrations)
- **Protection:** MEDIUM (captcha-protected)
- **Approach:** API + scraping with captcha solving
- **Fields:** CIN, company name, directors, capital, status, filings
- **Rate Limit:** Limited (requires care)
- **Compliance Risk:** LOW
- **Confidence:** 0.90
- **Implementation:** Phase 4 (Week 4)

### 16. GeM Portal
- **URL:** https://gem.gov.in/
- **Type:** Government e-Marketplace
- **Volume:** 1,000+ vendors/day
- **Protection:** LOW (official vendor directory)
- **Approach:** API Setu integration
- **Fields:** Vendor name, products, services, location, orders, rating
- **Rate Limit:** Unlimited (public data)
- **Compliance Risk:** LOW
- **Confidence:** 0.90
- **Implementation:** Phase 4 (Week 4)

### 17. MSME Udyam
- **URL:** https://udyamregistration.gov.in/
- **Type:** MSME Registration
- **Volume:** 2,000+ MSMEs/day
- **Protection:** LOW (official API via API Setu)
- **Approach:** API Setu client
- **Fields:** Enterprise name, Udyam number, owner, location, NIC code
- **Rate Limit:** As per API Setu limits
- **Compliance Risk:** LOW
- **Confidence:** 0.85
- **Implementation:** Phase 4 (Week 4)

### 18. API Setu
- **URL:** https://apisetu.gov.in/
- **Type:** Government API Gateway
- **Volume:** 4,200+ APIs
- **Protection:** LOW (official platform)
- **Approach:** Official API client
- **Fields:** Various government data
- **Rate Limit:** 6 crore transactions/month capacity
- **Compliance Risk:** LOW
- **Confidence:** 0.95
- **Implementation:** Phase 4 (Week 4)

---

## TIER 5: GOVERNMENT JOB PORTALS

### 19. Sarkari Result
- **URL:** https://www.sarkariresult.com/
- **Type:** Government Job Updates
- **Volume:** 500+ jobs/day
- **Protection:** LOW
- **Approach:** Direct parsing
- **Fields:** Post name, department, qualification, last date
- **Rate Limit:** Minimal
- **Compliance Risk:** LOW
- **Implementation:** Phase 5 (Week 5)

### 20. FreeJobAlert
- **URL:** https://www.freejobalert.com/
- **Type:** Government + Private Jobs
- **Volume:** 300+ jobs/day
- **Protection:** LOW
- **Approach:** Direct parsing
- **Fields:** Post name, department, qualification, last date
- **Rate Limit:** Minimal
- **Compliance Risk:** LOW
- **Implementation:** Phase 5 (Week 5)

### 21. Employment News
- **URL:** https://employmentnews.gov.in/
- **Type:** Official Government Jobs
- **Volume:** 100+ jobs/day
- **Protection:** LOW
- **Approach:** RSS feed
- **Fields:** Post name, department, qualification
- **Rate Limit:** RSS limits
- **Compliance Risk:** LOW
- **Implementation:** Phase 5 (Week 5)

---

## TIER 6: EXISTING SOCIAL SOURCES

| Source | URL | Type | Status |
|--------|-----|------|--------|
| Reddit | https://reddit.com | Social | ✅ Already integrated |
| HackerNews | https://news.ycombinator.com | Tech | ✅ Already integrated |
| GitHub | https://github.com | Code | ✅ Already integrated |
| StackOverflow | https://stackoverflow.com | Q&A | ✅ Already integrated |
| Twitter/X | https://twitter.com | Social | ⚠️ High risk |
| Telegram | https://telegram.org | Messaging | ✅ Already integrated |
| ProductHunt | https://producthunt.com | Launch | ✅ Already integrated |
| RSS | Various | Feed | ✅ Already integrated |

---

## COLLECTION STATISTICS

### By Tier

| Tier | Platforms | Daily Volume | Confidence |
|------|-----------|--------------|------------|
| 1 - Critical | 3 | 80,000+ | 0.75-0.80 |
| 2 - High Value | 4 | 25,000+ | 0.70-0.75 |
| 3 - Niche | 6 | 6,000+ | 0.65-0.70 |
| 4 - Government | 5 | 4,300+ | 0.85-0.95 |
| 5 - Govt Jobs | 3 | 900+ | 0.70-0.75 |
| 6 - Social | 8 | 2,000+ | 0.60-0.70 |
| **TOTAL** | **29** | **118,200+** | **0.78** |

### After Deduplication

| Source Type | Raw Volume | Unique Leads | Deduplication Rate |
|-------------|------------|--------------|-------------------|
| Job Platforms | 111,000 | 18,000 | 84% |
| Government | 4,300 | 3,500 | 19% |
| Social | 2,000 | 1,800 | 10% |
| **TOTAL** | **117,300** | **23,300** | **80%** |

**Target: 25,000 unique leads/day**

---

## SCRAPING APPROACH SUMMARY

| Approach | Platforms | Volume | Complexity |
|----------|-----------|--------|------------|
| API Interception | Naukri, LinkedIn | 70,000 | HIGH |
| Direct Parsing | Internshala, Indeed RSS | 25,000 | MEDIUM |
| Official API | DPIIT, GeM, MSME | 4,300 | LOW |
| Stealth Browser | Shine, Monster, Hirist | 13,000 | HIGH |
| RSS Feed | Indeed, Employment News | 15,100 | LOW |

---

## COMPLIANCE SUMMARY

| Risk Level | Platforms | Count |
|------------|-----------|-------|
| LOW | 12 | DPIIT, GeM, MSME, API Setu, Indeed RSS, Govt Jobs, Social |
| MEDIUM | 14 | Naukri, Internshala, Shine, Monster, LinkedIn, etc. |
| HIGH | 3 | Twitter/X, LinkedIn (fallback), Naukri (high volume) |
| CRITICAL | 0 | None (all manageable with proper approach) |

---

*Platform Catalog*
*Total Platforms: 29*
*Total Volume: 118,200+/day*
*Target Unique: 25,000/day*
*Date: 2026-05-11*
