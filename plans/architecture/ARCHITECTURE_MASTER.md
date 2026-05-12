# LeadIQ Optimized Architecture
> Designed using adaptive-imagining-cat methodology
> Research-driven system design
> Date: 2026-05-11

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      LEADIQ PLATFORM                         │
│              AI-Powered Lead Intelligence Engine             │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   COLLECTORS  │  │   PIPELINE   │  │   SERVICES   │
│  (Data Layer) │  │ (Flow Layer) │  │(Business Layer│
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    REDIS STREAMS HUB                        │
│                                                             │
│  lead:govt_collected    lead:jobs_collected   lead:social   │
│  lead:enriched          lead:scored           lead:ranked   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                 POSTGRESQL + PGVECTOR                        │
│                                                             │
│  posts    leads    feedback    quota_usage    user_profiles │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI + NEXTJS                          │
│                                                             │
│  /api/collect/*    /api/leads/*    /api/scoring/*           │
│  /api/analytics/*  /api/admin/*    /api/health              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Collectors Layer (Extended)

```python
class BaseCollector(ABC):
    """Abstract base for all data collectors"""
    
    source: str
    risk_level: RiskLevel
    rate_limit: RateLimitConfig
    proxy_config: ProxyConfig
    stealth_config: StealthConfig
    
    @abstractmethod
    async def collect(self) -> list[RawPost]:
        """Fetch and return new posts"""
        pass
    
    async def run(self) -> list[RawPost]:
        """Entry point with deduplication check"""
        posts = await self.collect()
        return await self.dedupe_filter(posts)
```

#### Government Collectors

```python
class DPIITCollector(BaseCollector):
    """DPIIT Startup India Registry"""
    source = "dpiit"
    risk_level = RiskLevel.low
    api_url = "https://api.startupindia.gov.in/sih/api/startup/search"
    
    async def collect(self) -> list[RawPost]:
        # Enhanced v2: More fields, cross-referencing
        startups = await self.fetch_startups(
            sectors=SECTORS,
            states=STATES,
            stages=["Ideation", "Validation", "Early Traction", "Scaling"]
        )
        return [self.transform(s) for s in startups]
    
    def transform(self, startup: dict) -> RawPost:
        return RawPost(
            source="dpiit",
            external_id=startup["id"],
            url=f"https://startupindia.gov.in/content/sih/en/search.html?q={startup['name']}",
            title=startup["name"],
            body=f"{startup['sector']} startup in {startup['city']}, {startup['state']}",
            author=startup.get("founder_name", ""),
            score=0,
            raw_meta={
                "sector": startup["sector"],
                "stage": startup["stage"],
                "state": startup["state"],
                "city": startup["city"],
                "founded_year": startup.get("inceptionDate", "")[:4],
                "website": startup.get("website"),
                "funding_stage": startup.get("stage"),
                "employees": startup.get("employeeCount"),
                "dpiit_recognized": True,
                "gst_number": startup.get("gstin"),
                "udyam_number": startup.get("udyam"),
            }
        )

class MCA21Collector(BaseCollector):
    """Ministry of Corporate Affairs"""
    source = "mca21"
    risk_level = RiskLevel.low
    
    async def collect(self) -> list[RawPost]:
        # Use Technowire API or direct scraping
        companies = await self.fetch_companies(
            search_type="active",
            class_type=["Private Limited", "Public Limited", "LLP"]
        )
        return [self.transform(c) for c in companies]

class GeMCollector(BaseCollector):
    """Government e-Marketplace"""
    source = "gem"
    risk_level = RiskLevel.low
    
    async def collect(self) -> list[RawPost]:
        vendors = await self.fetch_vendors(
            categories=["IT Services", "Software", "Consulting"],
            status="active"
        )
        return [self.transform(v) for v in vendors]

class MSMECollector(BaseCollector):
    """MSME Udyam Registration"""
    source = "msme"
    risk_level = RiskLevel.low
    
    async def collect(self) -> list[RawPost]:
        msmes = await self.fetch_msmes(
            sectors=SECTORS,
            states=STATES,
            nic_codes=NIC_CODES
        )
        return [self.transform(m) for m in msmes]
```

#### Job Platform Collectors

```python
class NaukriCollector(BaseCollector):
    """Naukri.com - India's largest job portal"""
    source = "naukri"
    risk_level = RiskLevel.medium
    
    # Anti-bot configuration
    stealth_config = StealthConfig(
        browser="playwright",
        stealth_plugins=["stealth", "user-agent-rotation"],
        proxy_type="residential",
        proxy_rotation=20,  # Rotate every 20 requests
        delay_range=(3, 5),  # 3-5 second delays
        tls_bypass="curl_cffi",
    )
    
    async def collect(self) -> list[RawPost]:
        # Strategy: API interception via Playwright
        browser = await self.launch_stealth_browser()
        
        jobs = []
        for keyword in self.target_keywords:
            for location in self.target_locations:
                page = await browser.new_page()
                
                # Navigate and intercept API calls
                await page.route("**/jobapi/v3/search", self.handle_api_response)
                await page.goto(f"https://www.naukri.com/{keyword}-jobs-in-{location}")
                
                # Extract from intercepted API responses
                api_data = await self.extract_api_data(page)
                jobs.extend(api_data)
                
                await page.close()
                await asyncio.sleep(random.uniform(3, 5))
        
        await browser.close()
        return [self.transform(j) for j in jobs]
    
    def transform(self, job: dict) -> RawPost:
        return RawPost(
            source="naukri",
            external_id=job["jobId"],
            url=f"https://www.naukri.com/job-listings-{job['jobId']}",
            title=job["title"],
            body=job["description"],
            author=job["companyName"],
            score=job.get("ambitionBoxRating", 0),
            raw_meta={
                "company_name": job["companyName"],
                "salary_min": job.get("salaryMin"),
                "salary_max": job.get("salaryMax"),
                "experience_min": job.get("experienceMin"),
                "experience_max": job.get("experienceMax"),
                "location": job["location"],
                "skills": job.get("skills", []),
                "work_mode": job.get("workMode"),  # remote/hybrid/office
                "job_type": job.get("jobType"),
                "posted_date": job.get("postedDate"),
                "apply_count": job.get("applyCount"),
                "ambition_box_rating": job.get("ambitionBoxRating"),
                "company_website": job.get("companyWebsite"),
            }
        )

class InternshalaCollector(BaseCollector):
    """Internshala - Top internship platform"""
    source = "internshala"
    risk_level = RiskLevel.low
    
    async def collect(self) -> list[RawPost]:
        # Direct HTML parsing with stealth headers
        async with httpx.AsyncClient(
            headers=self.stealth_headers,
            follow_redirects=True
        ) as client:
            internships = []
            for page_num in range(1, self.max_pages + 1):
                url = f"https://internshala.com/internships/page-{page_num}/"
                response = await client.get(url)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('div', class_='individual_internship')
                
                for card in cards:
                    internship = self.parse_card(card)
                    internships.append(internship)
                
                await asyncio.sleep(random.uniform(2, 4))
            
            return [self.transform(i) for i in internships]

class LinkedInJobsCollector(BaseCollector):
    """LinkedIn India Jobs"""
    source = "linkedin_jobs"
    risk_level = RiskLevel.high
    
    async def collect(self) -> list[RawPost]:
        # Use LinkedIn API if available
        # Fallback: Playwright with authenticated session
        
        jobs = await self.fetch_linkedin_jobs(
            keywords=self.target_keywords,
            location="India",
            time_filter="past_week"
        )
        return [self.transform(j) for j in jobs]
```

---

### 2. Scoring Engine (Research-Based)

```python
class HybridScoringEngine:
    """
    Hybrid ML + LLM scoring engine
    Based on: Gradient Boosting (Frontiers 2025) + asLLR (arXiv 2510.21713)
    """
    
    def __init__(self):
        # Component 1: Gradient Boosting (tabular features)
        self.gbm = GradientBoostingScorer()
        
        # Component 2: LLM (textual analysis)
        self.llm = LLMQualitativeScorer()
        
        # Component 3: RL (sequential optimization)
        self.rl = RLSequentialScorer()
        
        # Component 4: Uplift (revenue prediction)
        self.uplift = UpliftRevenueScorer()
        
        # Component 5: Geo-fairness
        self.geo = GeoFairnessScorer()
        
        # Weights (tuned via Optuna)
        self.weights = {
            'gbm': 0.30,
            'llm': 0.25,
            'rl': 0.20,
            'uplift': 0.15,
            'geo': 0.10
        }
    
    async def score(self, lead: Lead) -> ScoringResult:
        """Compute composite score using all components"""
        
        # Extract features
        tabular = self.extract_tabular_features(lead)
        textual = self.extract_textual_features(lead)
        sequential = self.extract_sequence_features(lead)
        
        # Component scores
        gbm_score = self.gbm.predict(tabular)
        llm_score = await self.llm.analyze(textual)
        rl_score = self.rl.predict(sequential)
        uplift_score = self.uplift.compute(lead)
        geo_score = self.geo.adjust(lead, lead.location)
        
        # Weighted ensemble
        final_score = (
            self.weights['gbm'] * gbm_score +
            self.weights['llm'] * llm_score +
            self.weights['rl'] * rl_score +
            self.weights['uplift'] * uplift_score +
            self.weights['geo'] * geo_score
        )
        
        # Band classification
        band = self.classify_band(final_score)
        
        return ScoringResult(
            final_score=final_score,
            band=band,
            component_scores={
                'gbm': gbm_score,
                'llm': llm_score,
                'rl': rl_score,
                'uplift': uplift_score,
                'geo': geo_score
            },
            confidence=self.compute_confidence(final_score),
            recommended_action=self.recommend_action(band),
            explanation=self.generate_explanation(lead, final_score)
        )
```

#### Feature Engineering

```python
class FeatureEngineer:
    """Feature engineering based on research findings"""
    
    def extract_tabular_features(self, lead: Lead) -> dict:
        """Extract structured features for GBM"""
        return {
            # Fit signals (30%)
            'source_encoded': self.encode_source(lead.source),
            'lead_status_encoded': self.encode_status(lead.stage),
            'company_size': self.encode_company_size(lead.company_size),
            'industry_match': self.compute_industry_match(lead.industry),
            'location_tier': self.encode_location_tier(lead.location),
            'govt_registered': int(bool(lead.gst_number or lead.udyam_number)),
            
            # Behavioral signals (35%)
            'page_views': lead.engagement_metrics.get('page_views', 0),
            'email_opens': lead.engagement_metrics.get('email_opens', 0),
            'email_clicks': lead.engagement_metrics.get('email_clicks', 0),
            'job_engagement': self.compute_job_engagement(lead),
            'content_downloads': lead.engagement_metrics.get('downloads', 0),
            
            # Intent signals (35%)
            'hiring_velocity': self.compute_hiring_velocity(lead),
            'funding_recency': self.compute_funding_recency(lead),
            'govt_tender_count': lead.raw_meta.get('tender_count', 0),
            'job_posting_count': lead.raw_meta.get('job_count', 0),
            'salary_range': self.encode_salary(lead.salary_range_min, lead.salary_range_max),
            
            # Indian-specific signals
            'dpiit_recognized': int(lead.source == 'dpiit'),
            'gst_verified': int(bool(lead.gst_number)),
            'udyam_verified': int(bool(lead.udyam_number)),
            'cin_verified': int(bool(lead.cin_number)),
            'gem_vendor': int(lead.source == 'gem'),
        }
    
    def extract_textual_features(self, lead: Lead) -> str:
        """Extract text for LLM analysis"""
        return f"""
        Company: {lead.company_name}
        Industry: {lead.industry}
        Description: {lead.raw_meta.get('description', '')}
        Job Requirements: {lead.raw_meta.get('job_description', '')}
        Recent News: {lead.raw_meta.get('recent_news', '')}
        Tech Stack: {', '.join(lead.raw_meta.get('tech_stack', []))}
        Funding: {lead.raw_meta.get('funding_stage', 'Unknown')}
        """
    
    def extract_sequence_features(self, lead: Lead) -> list:
        """Extract sequence for RL analysis"""
        return [
            {'action': 'collected', 'timestamp': lead.collected_at},
            {'action': 'analyzed', 'timestamp': lead.analyzed_at},
            {'action': 'scored', 'timestamp': lead.scored_at},
            {'action': 'enriched', 'timestamp': lead.enriched_at},
        ]
```

---

### 3. Pipeline Architecture

```yaml
pipeline:
  name: "leadiq-optimized-pipeline"
  version: "2.0"
  
  stages:
    - name: "collect"
      type: "parallel"
      collectors:
        - dpiit
        - mca21
        - gem
        - msme
        - naukri
        - internshala
        - linkedin_jobs
        - reddit
        - hn
        - github
      
    - name: "deduplicate"
      type: "sequential"
      method: "content_hash + vector_similarity"
      threshold: 0.92
      
    - name: "enrich"
      type: "parallel"
      services:
        - government_cross_reference
        - email_finder
        - company_verification
        - tech_stack_detection
      
    - name: "score"
      type: "sequential"
      engine: "hybrid_scoring"
      models:
        - gbm
        - llm
        - rl
        - uplift
        - geo
      
    - name: "rank"
      type: "sequential"
      method: "composite_score_descending"
      bands:
        hot: >= 75
        warm: 50-74
        cool: 25-49
        cold: < 25
      
    - name: "route"
      type: "parallel"
      rules:
        - if: "band == 'hot' and source == 'govt'"
          action: "immediate_outreach"
          priority: 1
        - if: "band == 'hot' and source == 'jobs'"
          action: "talent_acquisition_alert"
          priority: 2
        - if: "band == 'warm'"
          action: "nurture_sequence"
          priority: 3
        - if: "band == 'cold'"
          action: "long_term_nurture"
          priority: 4
```

---

### 4. Data Model Extensions

```python
# Enhanced Lead Model
class Lead(Base):
    __tablename__ = "leads"
    
    # Existing fields...
    
    # Government verification fields
    gst_number: str = Column(String(15), nullable=True, index=True)
    udyam_number: str = Column(String(16), nullable=True, index=True)
    cin_number: str = Column(String(21), nullable=True, index=True)
    company_type: str = Column(String(32), nullable=True)  # Pvt Ltd, LLP, etc.
    
    # Job-specific fields
    job_title: str = Column(String(256), nullable=True)
    experience_required: str = Column(String(32), nullable=True)
    salary_range_min: int = Column(Integer, nullable=True)
    salary_range_max: int = Column(Integer, nullable=True)
    skills: list = Column(ARRAY(String), nullable=True, default=[])
    work_mode: str = Column(String(16), nullable=True)  # remote/hybrid/office
    posted_date: datetime = Column(DateTime(timezone=True), nullable=True)
    
    # Scoring fields
    ml_score: float = Column(Float, default=0.0)
    llm_score: float = Column(Float, default=0.0)
    rl_score: float = Column(Float, default=0.0)
    uplift_score: float = Column(Float, default=0.0)
    geo_score: float = Column(Float, default=0.0)
    composite_score: float = Column(Float, default=0.0)
    
    # Pipeline fields
    band: str = Column(String(16), default="cold")
    routing_action: str = Column(String(32), nullable=True)
    outreach_priority: int = Column(Integer, default=4)
    
    # Enrichment fields
    email_verified: bool = Column(Boolean, default=False)
    phone_verified: bool = Column(Boolean, default=False)
    company_verified: bool = Column(Boolean, default=False)
    
    # Timestamps
    enriched_at: datetime = Column(DateTime(timezone=True), nullable=True)
    routed_at: datetime = Column(DateTime(timezone=True), nullable=True)
```

---

## API Design

### New Endpoints

```yaml
# Collection APIs
POST /api/collect/naukri
  body:
    keywords: ["python developer", "data scientist"]
    locations: ["bangalore", "hyderabad"]
    max_results: 1000

POST /api/collect/internshala
  body:
    categories: ["software engineering", "data science"]
    locations: ["remote", "bangalore"]
    max_results: 500

POST /api/collect/gem
  body:
    categories: ["IT Services", "Software"]
    states: ["Karnataka", "Maharashtra"]

POST /api/collect/mca21
  body:
    search_type: "active"
    company_types: ["Private Limited", "LLP"]
    states: ["Karnataka"]

# Lead APIs
GET /api/leads/government
  query:
    source: ["dpiit", "mca21", "gem", "msme"]
    state: "Karnataka"
    sector: "Technology"
    band: "hot"

GET /api/leads/jobs
  query:
    source: ["naukri", "internshala", "linkedin"]
    skills: ["python", "react"]
    experience: "0-3 years"
    work_mode: "remote"

GET /api/leads/analytics
  query:
    metric: "conversion_rate"
    group_by: "source"
    time_range: "last_30_days"

POST /api/scoring/batch
  body:
    lead_ids: ["uuid1", "uuid2", "uuid3"]
    force_recalculate: true

GET /api/scoring/explain
  query:
    lead_id: "uuid"
    # Returns feature importance breakdown
```

---

## Infrastructure

```yaml
docker-compose:
  services:
    backend:
      image: leadiq-backend:latest
      environment:
        - DATABASE_URL=postgresql+asyncpg://...
        - REDIS_URL=redis://redis:6379
        - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
      volumes:
        - proxy-pool:/app/proxies
    
    redis:
      image: redis:7-alpine
      command: redis-server --appendonly yes
    
    postgres:
      image: pgvector/pgvector:pg16
      volumes:
        - postgres-data:/var/lib/postgresql/data
    
    playwright:
      image: mcr.microsoft.com/playwright:v1.40.0-focal
      volumes:
        - /tmp/.X11-unix:/tmp/.X11-unix
    
    celery-worker:
      image: leadiq-backend:latest
      command: celery -A backend.workers.pipeline worker -l info
      environment:
        - CELERY_BROKER_URL=redis://redis:6379/0
    
    scraper-scheduler:
      image: leadiq-backend:latest
      command: python -m backend.schedulers.scraper_scheduler
      environment:
        - SCHEDULE_NAUKRI=*/6 * * * *  # Every 6 hours
        - SCHEDULE_INTERNSHALA=*/12 * * * *  # Every 12 hours
        - SCHEDULE_GOVT=*/24 * * * *  # Daily
```

---

*Architecture designed using research-backed patterns*
*Date: 2026-05-11*
*Version: 2.0*
