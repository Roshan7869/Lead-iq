# Phases 2-3: Job Platform Collectors (Naukri + Internshala)
> Duration: Week 2-3
> Priority: CRITICAL
> Dependencies: Phase 1 (Foundation)
> Research Basis: asLLR (arXiv 2510.21713), Scrapus (Frontiers 2025)

---

## Phase 2: Naukri.com Collector

### Objective
Deploy production-grade Naukri.com scraper using API interception + Playwright stealth.

### Implementation

```python
# backend/collectors/naukri.py
"""
naukri.py - Naukri.com job scraper with API interception
India's largest job portal: https://www.naukri.com/
~50,000 jobs/day
"""
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
import structlog
from bs4 import BeautifulSoup

from backend.collectors.base import BaseCollector, RawPost
from backend.collectors.scraping_utils import ScrapingUtils, StealthConfig
from backend.collectors.stealth_session import StealthSession

logger = structlog.get_logger()

class NaukriCollector(BaseCollector):
    """Naukri.com collector with API interception"""
    
    source = "naukri"
    BASE_URL = "https://www.naukri.com"
    API_PATTERN = "**/jobapi/v3/search"
    
    def __init__(self):
        self.config = StealthConfig(
            browser="playwright",
            proxy_type="residential",
            proxy_rotation_interval=20,
            delay_min=3.0,
            delay_max=5.0,
            tls_bypass="curl_cffi",
        )
        self.utils = ScrapingUtils(self.config)
        self.intercepted_data: List[Dict] = []
        
    async def collect(self) -> List[RawPost]:
        """Collect jobs from Naukri.com"""
        
        all_jobs = []
        
        for keyword in self.target_keywords:
            for location in self.target_locations:
                try:
                    jobs = await self._scrape_search(keyword, location)
                    all_jobs.extend(jobs)
                    logger.info("naukri_search_complete",
                               keyword=keyword,
                               location=location,
                               jobs_found=len(jobs))
                except Exception as e:
                    logger.error("naukri_search_failed",
                                keyword=keyword,
                                location=location,
                                error=str(e))
                    
                await self.utils.random_delay()
                
        return all_jobs
        
    async def _scrape_search(self, keyword: str, location: str) -> List[RawPost]:
        """Scrape jobs for specific keyword + location"""
        
        session = await self.utils.create_stealth_session()
        
        try:
            await session.start()
            
            # Set up API interception
            await session.intercept_api(
                "jobapi/v3/search",
                self._handle_api_response
            )
            
            # Navigate to search page
            search_url = f"{self.BASE_URL}/{keyword.replace(' ', '-')}-jobs-in-{location}"
            await session.goto(search_url)
            
            # Wait for API responses
            await asyncio.sleep(5)
            
            # Process intercepted data
            jobs = []
            for api_response in self.intercepted_data:
                job_listings = self._parse_api_response(api_response)
                jobs.extend(job_listings)
                
            # Fallback: Parse HTML if API interception fails
            if not jobs:
                logger.warning("api_interception_failed_using_html_fallback")
                jobs = await self._parse_html(session.page)
                
            return [self.transform(job) for job in jobs]
            
        finally:
            await session.close()
            self.intercepted_data = []
            
    async def _handle_api_response(self, body: Dict):
        """Handle intercepted API response"""
        self.intercepted_data.append(body)
        
    def _parse_api_response(self, response: Dict) -> List[Dict]:
        """Parse job listings from API response"""
        jobs = []
        
        if "jobAds" in response:
            for job in response["jobAds"]:
                jobs.append({
                    "jobId": job.get("jobId"),
                    "title": job.get("title"),
                    "companyName": job.get("companyName"),
                    "description": job.get("jobDescription"),
                    "location": job.get("placeholders", {}).get("location"),
                    "experience": job.get("placeholders", {}).get("experience"),
                    "salary": job.get("placeholders", {}).get("salary"),
                    "skills": job.get("tagsAndSkills", []),
                    "workMode": job.get("workFromHomeType"),
                    "jobType": job.get("jobType"),
                    "postedDate": job.get("footerPlaceholderLabel"),
                    "applyCount": job.get("applyCount"),
                    "ambitionBoxRating": job.get("ambitionBoxData", {}).get("rating"),
                })
                
        return jobs
        
    async def _parse_html(self, page) -> List[Dict]:
        """Fallback HTML parsing"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        jobs = []
        job_cards = soup.find_all('article', class_='jobTuple')
        
        for card in job_cards:
            job = {
                "title": self._safe_extract(card, '.title'),
                "companyName": self._safe_extract(card, '.company-name'),
                "location": self._safe_extract(card, '.location'),
                "experience": self._safe_extract(card, '.experience'),
                "salary": self._safe_extract(card, '.salary'),
            }
            jobs.append(job)
            
        return jobs
        
    def transform(self, job: Dict) -> RawPost:
        """Transform Naukri job to RawPost"""
        
        # Parse salary range
        salary_min, salary_max = self._parse_salary(job.get("salary", ""))
        
        # Parse experience
        exp_min, exp_max = self._parse_experience(job.get("experience", ""))
        
        return RawPost(
            source="naukri",
            external_id=job.get("jobId", "unknown"),
            url=f"{self.BASE_URL}/job-listings-{job.get('jobId', '')}",
            title=job.get("title", ""),
            body=job.get("description", ""),
            author=job.get("companyName", ""),
            score=job.get("ambitionBoxRating", 0),
            raw_meta={
                "company_name": job.get("companyName"),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_min": exp_min,
                "experience_max": exp_max,
                "location": job.get("location"),
                "skills": job.get("skills", []),
                "work_mode": job.get("workMode"),
                "job_type": job.get("jobType"),
                "posted_date": job.get("postedDate"),
                "apply_count": job.get("applyCount"),
                "ambition_box_rating": job.get("ambitionBoxRating"),
            }
        )
        
    def _parse_salary(self, salary_str: str) -> tuple:
        """Parse salary string to min/max"""
        try:
            # Handle formats: "₹5-10 LPA", "₹5 Lacs - 10 Lacs P.A.", etc.
            import re
            numbers = re.findall(r'(\d+)', salary_str)
            if len(numbers) >= 2:
                return int(numbers[0]) * 100000, int(numbers[1]) * 100000
            elif len(numbers) == 1:
                return int(numbers[0]) * 100000, int(numbers[0]) * 100000
        except:
            pass
        return None, None
        
    def _parse_experience(self, exp_str: str) -> tuple:
        """Parse experience string to min/max years"""
        try:
            import re
            numbers = re.findall(r'(\d+)', exp_str)
            if len(numbers) >= 2:
                return int(numbers[0]), int(numbers[1])
            elif len(numbers) == 1:
                return int(numbers[0]), int(numbers[0])
        except:
            pass
        return None, None
        
    def _safe_extract(self, soup, selector: str) -> str:
        """Safely extract text from soup"""
        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else ""
        
    @property
    def target_keywords(self) -> List[str]:
        return [
            "software engineer",
            "data scientist",
            "product manager",
            "devops engineer",
            "frontend developer",
            "backend developer",
            "full stack developer",
            "machine learning engineer",
            "cloud architect",
            "cybersecurity analyst",
        ]
        
    @property
    def target_locations(self) -> List[str]:
        return [
            "bangalore",
            "hyderabad",
            "pune",
            "chennai",
            "mumbai",
            "delhi",
            "gurgaon",
            "noida",
        ]
```

---

## Phase 3: Internshala Collector

### Objective
Deploy Internshala internship scraper with direct HTML parsing.

### Implementation

```python
# backend/collectors/internshala.py
"""
internshala.py - Internshala internship scraper
Top internship platform: https://internshala.com/
~10,000 internships/day
"""
import asyncio
from typing import List
import structlog
import httpx
from bs4 import BeautifulSoup

from backend.collectors.base import BaseCollector, RawPost
from backend.collectors.scraping_utils import ScrapingUtils, StealthConfig

logger = structlog.get_logger()

class InternshalaCollector(BaseCollector):
    """Internshala internship collector"""
    
    source = "internshala"
    BASE_URL = "https://internshala.com"
    
    def __init__(self):
        self.config = StealthConfig(
            delay_min=2.0,
            delay_max=4.0,
        )
        self.utils = ScrapingUtils(self.config)
        
    async def collect(self) -> List[RawPost]:
        """Collect internships from Internshala"""
        
        all_internships = []
        
        async with httpx.AsyncClient(
            headers=self._get_headers(),
            follow_redirects=True,
            timeout=30.0
        ) as client:
            
            for category in self.target_categories:
                try:
                    internships = await self._scrape_category(client, category)
                    all_internships.extend(internships)
                    logger.info("internshala_category_complete",
                               category=category,
                               count=len(internships))
                except Exception as e:
                    logger.error("internshala_category_failed",
                                category=category,
                                error=str(e))
                    
                await self.utils.random_delay()
                
        return all_internships
        
    def _get_headers(self) -> dict:
        """Get stealth headers"""
        return {
            "User-Agent": self.utils.ua_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        
    async def _scrape_category(self, client: httpx.AsyncClient, category: str) -> List[RawPost]:
        """Scrape internships for a category"""
        
        internships = []
        page = 1
        
        while page <= self.max_pages:
            url = f"{self.BASE_URL}/internships/{category}/page-{page}/"
            
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('div', class_='individual_internship')
                
                if not cards:
                    break
                    
                for card in cards:
                    internship = self._parse_card(card)
                    if internship:
                        internships.append(internship)
                        
                page += 1
                await self.utils.random_delay()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    break
                raise
                
        return internships
        
    def _parse_card(self, card) -> Optional[RawPost]:
        """Parse internship card"""
        try:
            # Extract fields
            title = card.find('h3', class_='job-internship-name')
            company = card.find('h4', class_='company-name')
            location = card.find('a', id='location_names')
            
            # Stipend
            stipend_elem = card.find('span', class_='stipend')
            stipend_min, stipend_max = self._parse_stipend(
                stipend_elem.get_text(strip=True) if stipend_elem else ""
            )
            
            # Duration
            duration_elem = card.find('div', id='duration")
            duration = duration_elem.get_text(strip=True) if duration_elem else ""
            
            # Posted date
            posted_elem = card.find('div', class_='status-success')
            posted = posted_elem.get_text(strip=True) if posted_elem else ""
            
            # Apply link
            link_elem = card.find('a', class_='view_detail_button')
            link = f"{self.BASE_URL}{link_elem['href']}" if link_elem else ""
            
            return RawPost(
                source="internshala",
                external_id=self._extract_id(link),
                url=link,
                title=title.get_text(strip=True) if title else "",
                body=f"Internship at {company.get_text(strip=True) if company else 'Unknown'}",
                author=company.get_text(strip=True) if company else "",
                score=0,
                raw_meta={
                    "company_name": company.get_text(strip=True) if company else "",
                    "location": location.get_text(strip=True) if location else "",
                    "stipend_min": stipend_min,
                    "stipend_max": stipend_max,
                    "duration": duration,
                    "posted_date": posted,
                    "category": "internship",
                    "is_work_from_home": "work from home" in card.get_text().lower(),
                    "is_part_time": "part time" in card.get_text().lower(),
                }
            )
            
        except Exception as e:
            logger.warning("internshala_card_parse_failed", error=str(e))
            return None
            
    def _parse_stipend(self, stipend_str: str) -> tuple:
        """Parse stipend string"""
        try:
            import re
            numbers = re.findall(r'(\d+)', stipend_str)
            if len(numbers) >= 2:
                return int(numbers[0]), int(numbers[1])
            elif len(numbers) == 1:
                return int(numbers[0]), int(numbers[0])
        except:
            pass
        return None, None
        
    def _extract_id(self, url: str) -> str:
        """Extract internship ID from URL"""
        import re
        match = re.search(r'/internship/detail/(.+)', url)
        return match.group(1) if match else "unknown"
        
    @property
    def target_categories(self) -> List[str]:
        return [
            "software-development",
            "data-science",
            "web-development",
            "android-app-development",
            "ios-development",
            "machine-learning",
            "cloud-computing",
            "cyber-security",
        ]
        
    @property
    def max_pages(self) -> int:
        return 10
```

---

## Verification Checkpoints

### Checkpoint 2.1: Naukri Collection
- [ ] Extract 1000+ jobs in single run
- [ ] Salary parsing accuracy > 90%
- [ ] Experience parsing accuracy > 90%
- [ ] No IP blocks during 100 requests
- [ ] API interception success rate > 80%

### Checkpoint 2.2: Internshala Collection
- [ ] Extract 500+ internships in single run
- [ ] Stipend parsing accuracy > 90%
- [ ] No blocks during 50 requests
- [ ] Handle pagination correctly

---

## Testing

```python
# tests/collectors/test_naukri.py
import pytest
from backend.collectors.naukri import NaukriCollector

@pytest.mark.asyncio
async def test_naukri_collection():
    collector = NaukriCollector()
    jobs = await collector.collect()
    
    assert len(jobs) > 0
    assert all(j.source == "naukri" for j in jobs)
    assert all(j.title for j in jobs)
    assert all(j.raw_meta.get("company_name") for j in jobs)

@pytest.mark.asyncio
async def test_naukri_salary_parsing():
    collector = NaukriCollector()
    
    test_cases = [
        ("₹5-10 LPA", 500000, 1000000),
        ("₹15 Lacs P.A.", 1500000, 1500000),
        ("Not Disclosed", None, None),
    ]
    
    for input_str, expected_min, expected_max in test_cases:
        min_val, max_val = collector._parse_salary(input_str)
        assert min_val == expected_min
        assert max_val == expected_max

# tests/collectors/test_internshala.py
import pytest
from backend.collectors.internshala import InternshalaCollector

@pytest.mark.asyncio
async def test_internshala_collection():
    collector = InternshalaCollector()
    internships = await collector.collect()
    
    assert len(internships) > 0
    assert all(i.source == "internshala" for i in internships)
```

---

## Files to Create
- `backend/collectors/naukri.py`
- `backend/collectors/internshala.py`
- `workers/naukri-actor/main.py`
- `workers/internshala-actor/main.py`
- `workers/naukri-actor/requirements.txt`
- `workers/internshala-actor/requirements.txt`
- `tests/collectors/test_naukri.py`
- `tests/collectors/test_internshala.py`

---

*Phases 2-3 - Job Platform Collectors*
*Duration: Week 2-3*
*Estimated leads/day: 60,000+ (Naukri + Internshala)*
