# Phases 4-5: Government API Collectors
> Duration: Week 4-5
> Priority: HIGH
> Dependencies: Phase 1 (Foundation)
> Research Basis: API Setu, MCA21 V3, DPIIT Registry

---

## Phase 4: Government API Integration

### Objective
Integrate official Indian government data sources via API Setu and direct APIs.

### 4.1 API Setu Integration

```python
# backend/collectors/apisetu_client.py
"""
API Setu client for government data access
Platform: https://apisetu.gov.in/
4,200+ APIs, 1,800+ partners, 6 crore transactions/month
"""
import httpx
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

class APISetuClient:
    """Client for API Setu platform"""
    
    BASE_URL = "https://apisetu.gov.in/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0
        )
        
    async def search_apis(self, category: str = None) -> List[Dict]:
        """Search available APIs"""
        params = {}
        if category:
            params["category"] = category
            
        response = await self.client.get(
            f"{self.BASE_URL}/apis",
            params=params
        )
        response.raise_for_status()
        return response.json().get("apis", [])
        
    async def call_api(self, api_id: str, endpoint: str, params: Dict) -> Dict:
        """Call specific API endpoint"""
        response = await self.client.get(
            f"{self.BASE_URL}/{api_id}/{endpoint}",
            params=params
        )
        response.raise_for_status()
        return response.json()
```

### 4.2 DPIIT Enhanced Collector

```python
# backend/collectors/dpiit_v2.py
"""
DPIIT Startup India Collector v2
Enhanced with more fields and cross-referencing
API: https://api.startupindia.gov.in/sih/api/startup/search
"""
import httpx
from typing import List, Dict, Optional
import structlog

from backend.collectors.base import BaseCollector, RawPost

logger = structlog.get_logger()

class DPIITv2Collector(BaseCollector):
    """Enhanced DPIIT collector with full field extraction"""
    
    source = "dpiit_v2"
    API_URL = "https://api.startupindia.gov.in/sih/api/startup/search"
    
    SECTORS = [
        "Technology", "Healthcare", "Education", "Finance",
        "Agriculture", "Manufacturing", "E-commerce",
        "Fintech", "Edtech", "Healthtech", "AI/ML",
        "Blockchain", "IoT", "Clean Energy", "Space",
    ]
    
    STATES = [
        "Karnataka", "Maharashtra", "Telangana", "Tamil Nadu",
        "Delhi", "Gujarat", "Rajasthan", "Madhya Pradesh",
        "Uttar Pradesh", "West Bengal", "Odisha", "Kerala",
        "Punjab", "Haryana", "Bihar", "Jharkhand",
    ]
    
    async def collect(self) -> List[RawPost]:
        """Collect startups from DPIIT"""
        
        all_startups = []
        
        for sector in self.SECTORS:
            for state in self.STATES:
                try:
                    startups = await self._fetch_startups(sector, state)
                    all_startups.extend(startups)
                    logger.info("dpiit_fetch_complete",
                               sector=sector,
                               state=state,
                               count=len(startups))
                except Exception as e:
                    logger.error("dpiit_fetch_failed",
                                sector=sector,
                                state=state,
                                error=str(e))
                    
        return all_startups
        
    async def _fetch_startups(self, sector: str, state: str) -> List[RawPost]:
        """Fetch startups for sector + state"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "sector": sector,
                "state": state,
                "stage": ["Ideation", "Validation", "Early Traction", "Scaling"],
                "pageNo": 0,
                "pageSize": 100,
            }
            
            response = await client.post(
                self.API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
            response.raise_for_status()
            
            data = response.json()
            startups = data.get("data", [])
            
            return [self.transform(s) for s in startups]
            
    def transform(self, startup: Dict) -> RawPost:
        """Transform DPIIT startup to RawPost"""
        
        return RawPost(
            source="dpiit_v2",
            external_id=startup.get("id", "unknown"),
            url=f"https://startupindia.gov.in/content/sih/en/search.html?q={startup.get('name', '')}",
            title=startup.get("name", ""),
            body=f"{startup.get('sector', '')} startup in {startup.get('city', '')}, {startup.get('state', '')}",
            author=startup.get("founderName", ""),
            score=0,
            raw_meta={
                # Basic info
                "company_name": startup.get("name"),
                "sector": startup.get("sector"),
                "sub_sector": startup.get("subSector"),
                "stage": startup.get("stage"),
                "state": startup.get("state"),
                "city": startup.get("city"),
                
                # Legal info
                "legal_name": startup.get("legalName"),
                "cin": startup.get("cin"),
                "incorporation_date": startup.get("incorporationDate"),
                "incorporation_type": startup.get("incorporationType"),
                
                # Contact info
                "website": startup.get("website"),
                "email": startup.get("email"),
                "mobile": startup.get("mobile"),
                
                # Founder info
                "founder_name": startup.get("founderName"),
                "founder_email": startup.get("founderEmail"),
                "founder_mobile": startup.get("founderMobile"),
                "founder_gender": startup.get("founderGender"),
                
                # Business details
                "employees": startup.get("employeeCount"),
                "revenue": startup.get("revenue"),
                "funding_stage": startup.get("stage"),
                "investors": startup.get("investorNames", []),
                "funding_amount": startup.get("fundingAmount"),
                
                # DPIIT specific
                "dpiit_recognized": True,
                "dpiit_certificate": startup.get("dpiitCertificateNumber"),
                "recognition_date": startup.get("dpiitRecognitionDate"),
                "udyam_number": startup.get("udyamNumber"),
                "gst_number": startup.get("gstin"),
                "pan": startup.get("pan"),
                
                # Scoring signals
                "is_women_led": startup.get("isWomenLed", False),
                "is_social_impact": startup.get("isSocialImpact", False),
                "patents_filed": startup.get("patentsFiled", 0),
                "trademarks": startup.get("trademarks", 0),
            }
        )
```

### 4.3 MCA21 Collector

```python
# backend/collectors/mca21_v2.py
"""
MCA21 Corporate Data Collector
Ministry of Corporate Affairs: https://www.mca.gov.in/
"""
import httpx
import re
from typing import List, Dict, Optional
import structlog

from backend.collectors.base import BaseCollector, RawPost

logger = structlog.get_logger()

class MCA21Collector(BaseCollector):
    """MCA21 company data collector"""
    
    source = "mca21"
    SEARCH_URL = "https://www.mca.gov.in/bin/searchCompanyName"
    DETAILS_URL = "https://www.mca.gov.in/bin/MCA21/companyMasterData"
    
    async def collect(self) -> List[RawPost]:
        """Collect company data from MCA21"""
        
        companies = []
        
        # Search by CIN patterns for active companies
        for pattern in self._generate_cin_patterns():
            try:
                results = await self._search_by_pattern(pattern)
                companies.extend(results)
            except Exception as e:
                logger.error("mca21_search_failed", pattern=pattern, error=str(e))
                
        return [self.transform(c) for c in companies]
        
    async def _search_by_pattern(self, pattern: str) -> List[Dict]:
        """Search companies by CIN pattern"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.SEARCH_URL,
                params={"searchWord": pattern}
            )
            response.raise_for_status()
            return response.json().get("results", [])
            
    async def _get_company_details(self, cin: str) -> Dict:
        """Get detailed company info by CIN"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.DETAILS_URL,
                params={"cin": cin}
            )
            response.raise_for_status()
            return response.json()
            
    def _generate_cin_patterns(self) -> List[str]:
        """Generate CIN search patterns for recent companies"""
        # CIN format: U74999MH2020PTC345678
        # Focus on recent years
        years = range(2020, 2026)
        states = ["MH", "KA", "TG", "TN", "DL", "GJ"]
        
        patterns = []
        for year in years:
            for state in states:
                patterns.append(f"U{state}{year}")
                
        return patterns
        
    def transform(self, company: Dict) -> RawPost:
        """Transform MCA21 company to RawPost"""
        
        cin = company.get("cin", "")
        parsed_cin = self._parse_cin(cin)
        
        return RawPost(
            source="mca21",
            external_id=cin,
            url=f"https://www.mca.gov.in/mcafoportal/showCompanyMasterData.do?cin={cin}",
            title=company.get("companyName", ""),
            body=f"{company.get('companyType', '')} company in {company.get('registeredOfficeState', '')}",
            author="",
            score=0,
            raw_meta={
                "company_name": company.get("companyName"),
                "cin": cin,
                "company_type": company.get("companyType"),
                "company_status": company.get("companyStatus"),
                "incorporation_date": company.get("dateOfIncorporation"),
                "incorporation_year": parsed_cin.get("year"),
                "state": company.get("registeredOfficeState"),
                "city": company.get("registeredOfficeCity"),
                "address": company.get("registeredOfficeAddress"),
                "email": company.get("email"),
                "authorized_capital": company.get("authorizedCapital"),
                "paid_up_capital": company.get("paidUpCapital"),
                "industry": company.get("industry"),
                "nic_code": company.get("nicCode"),
                "directors": company.get("directors", []),
                "registrar": company.get("registrarOfCompanies"),
                "is_active": company.get("companyStatus") == "Active",
                "gst_number": company.get("gstin"),
            }
        )
        
    def _parse_cin(self, cin: str) -> Dict:
        """Parse CIN to extract components"""
        pattern = r"^([A-Z])(\d{5})([A-Z]{2})(\d{4})([A-Z]{3})(\d{6})$"
        match = re.match(pattern, cin)
        
        if not match:
            return {}
            
        return {
            "type": match.group(1),
            "nic": match.group(2),
            "state": match.group(3),
            "year": match.group(4),
            "entity": match.group(5),
            "unique": match.group(6),
        }
```

### 4.4 GeM Portal Collector

```python
# backend/collectors/gem.py
"""
GeM Portal Vendor Collector
Government e-Marketplace: https://gem.gov.in/
"""
import httpx
from typing import List, Dict
import structlog

from backend.collectors.base import BaseCollector, RawPost

logger = structlog.get_logger()

class GeMCollector(BaseCollector):
    """GeM Portal vendor collector"""
    
    source = "gem"
    SEARCH_URL = "https://mkp.gem.gov.in/api/search"
    
    async def collect(self) -> List[RawPost]:
        """Collect vendors from GeM Portal"""
        
        vendors = []
        
        for category in self.target_categories:
            try:
                results = await self._search_vendors(category)
                vendors.extend(results)
                logger.info("gem_search_complete",
                           category=category,
                           count=len(results))
            except Exception as e:
                logger.error("gem_search_failed",
                            category=category,
                            error=str(e))
                
        return [self.transform(v) for v in vendors]
        
    async def _search_vendors(self, category: str) -> List[Dict]:
        """Search vendors by category"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.SEARCH_URL,
                params={
                    "search_type": "vendor",
                    "category": category,
                    "status": "active",
                }
            )
            response.raise_for_status()
            return response.json().get("vendors", [])
            
    def transform(self, vendor: Dict) -> RawPost:
        """Transform GeM vendor to RawPost"""
        
        return RawPost(
            source="gem",
            external_id=vendor.get("vendorId", "unknown"),
            url=f"https://mkp.gem.gov.in/vendor/{vendor.get('vendorId', '')}",
            title=vendor.get("firmName", ""),
            body=f"{vendor.get('category', '')} vendor - {vendor.get('description', '')}",
            author=vendor.get("contactPerson", ""),
            score=vendor.get("rating", 0),
            raw_meta={
                "company_name": vendor.get("firmName"),
                "vendor_id": vendor.get("vendorId"),
                "category": vendor.get("category"),
                "sub_category": vendor.get("subCategory"),
                "state": vendor.get("state"),
                "city": vendor.get("city"),
                "address": vendor.get("address"),
                "contact_person": vendor.get("contactPerson"),
                "contact_email": vendor.get("email"),
                "contact_phone": vendor.get("phone"),
                "pan": vendor.get("pan"),
                "gst_number": vendor.get("gstin"),
                "udyam_number": vendor.get("udyam"),
                "registration_date": vendor.get("registrationDate"),
                "is_active": vendor.get("status") == "Active",
                "products": vendor.get("products", []),
                "services": vendor.get("services", []),
                "tender_history": vendor.get("tenderHistory", []),
                "rating": vendor.get("rating"),
                "total_orders": vendor.get("totalOrders", 0),
                "total_value": vendor.get("totalValue", 0),
            }
        )
        
    @property
    def target_categories(self) -> List[str]:
        return [
            "IT Services",
            "Software",
            "Consulting",
            "Cloud Services",
            "Cybersecurity",
            "Data Analytics",
            "AI/ML Services",
            "Digital Marketing",
        ]
```

### 4.5 MSME Udyam Collector

```python
# backend/collectors/msme.py
"""
MSME Udyam Registration Collector
10M+ registered MSMEs
"""
import httpx
from typing import List, Dict
import structlog

from backend.collectors.base import BaseCollector, RawPost

logger = structlog.get_logger()

class MSMECollector(BaseCollector):
    """MSME Udyam registration collector"""
    
    source = "msme"
    API_URL = "https://udyamregistration.gov.in/UdyamRegistration.aspx"
    
    # NIC codes for IT/Software
    TARGET_NIC_CODES = [
        "62011", "62012", "62013",  # Computer programming
        "62020",  # Computer consultancy
        "62021", "62022",  # Software publishing
        "63110", "63120",  # Data processing
        "63111", "63112",  # Web hosting
        "63911", "63912",  # Internet services
    ]
    
    async def collect(self) -> List[RawPost]:
        """Collect MSME registrations"""
        
        msmes = []
        
        for state in self.target_states:
            for nic in self.TARGET_NIC_CODES:
                try:
                    results = await self._search_msme(state, nic)
                    msmes.extend(results)
                    logger.info("msme_search_complete",
                               state=state,
                               nic=nic,
                               count=len(results))
                except Exception as e:
                    logger.error("msme_search_failed",
                                state=state,
                                nic=nic,
                                error=str(e))
                    
        return [self.transform(m) for m in msmes]
        
    async def _search_msme(self, state: str, nic: str) -> List[Dict]:
        """Search MSME by state and NIC code"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.API_URL,
                params={
                    "search": "enterprise",
                    "state": state,
                    "nic": nic,
                    "status": "active",
                }
            )
            response.raise_for_status()
            return response.json().get("enterprises", [])
            
    def transform(self, msme: Dict) -> RawPost:
        """Transform MSME to RawPost"""
        
        return RawPost(
            source="msme",
            external_id=msme.get("udyamNumber", "unknown"),
            url=f"https://udyamregistration.gov.in/PrintUdyamCertificate.aspx?uin={msme.get('udyamNumber', '')}",
            title=msme.get("enterpriseName", ""),
            body=f"{msme.get('nicDescription', '')} MSME in {msme.get('state', '')}",
            author=msme.get("ownerName", ""),
            score=0,
            raw_meta={
                "enterprise_name": msme.get("enterpriseName"),
                "udyam_number": msme.get("udyamNumber"),
                "owner_name": msme.get("ownerName"),
                "owner_email": msme.get("ownerEmail"),
                "owner_phone": msme.get("ownerPhone"),
                "state": msme.get("state"),
                "district": msme.get("district"),
                "city": msme.get("city"),
                "address": msme.get("address"),
                "nic_code": msme.get("nicCode"),
                "nic_description": msme.get("nicDescription"),
                "organization_type": msme.get("organizationType"),
                "registration_date": msme.get("registrationDate"),
                "major_activity": msme.get("majorActivity"),
                "social_category": msme.get("socialCategory"),
                "gender": msme.get("gender"),
                "is_women_owned": msme.get("isWomenOwned", False),
                "is_sc_st": msme.get("isScSt", False),
                "is_backward_class": msme.get("isBackwardClass", False),
                "unit_location": msme.get("unitLocation"),
                "unit_type": msme.get("unitType"),
            }
        )
        
    @property
    def target_states(self) -> List[str]:
        return [
            "Karnataka", "Maharashtra", "Telangana", "Tamil Nadu",
            "Delhi", "Gujarat", "Rajasthan", "Madhya Pradesh",
        ]
```

---

## Phase 5: Cross-Reference Pipeline

### Objective
Build pipeline to cross-reference and enrich data across government sources.

```python
# backend/services/govt_cross_reference.py
"""
Government data cross-reference service
Links: CIN ↔ DPIIT ↔ GST ↔ MSME
"""
from typing import Dict, Optional, List
import structlog

logger = structlog.get_logger()

class GovtCrossReferenceService:
    """Cross-reference government data sources"""
    
    def __init__(self):
        self.dpiit_client = DPIITv2Collector()
        self.mca_client = MCA21Collector()
        self.gem_client = GeMCollector()
        self.msme_client = MSMECollector()
        
    async def enrich_lead(self, lead: Lead) -> EnrichedLead:
        """Enrich lead with government data cross-referencing"""
        
        enriched = EnrichedLead(**lead.__dict__)
        
        # Try to find by CIN
        if lead.cin_number:
            mca_data = await self.mca_client._get_company_details(lead.cin_number)
            if mca_data:
                enriched = self._merge_mca_data(enriched, mca_data)
                
        # Try to find by GST
        if lead.gst_number:
            gst_data = await self._verify_gst(lead.gst_number)
            if gst_data:
                enriched = self._merge_gst_data(enriched, gst_data)
                
        # Try to find by Udyam
        if lead.udyam_number:
            msme_data = await self.msme_client._search_msme(
                state=lead.location,
                nic=None
            )
            if msme_data:
                enriched = self._merge_msme_data(enriched, msme_data)
                
        # Try to find in GeM
        gem_data = await self.gem_client._search_vendors(
            category=lead.industry
        )
        if gem_data:
            enriched = self._merge_gem_data(enriched, gem_data)
            
        # Calculate verification score
        enriched.govt_verification_score = self._calculate_verification_score(enriched)
        
        return enriched
        
    def _calculate_verification_score(self, lead: EnrichedLead) -> float:
        """Calculate government verification score (0-1)"""
        
        score = 0.0
        
        # CIN verification (MCA21) - 0.25
        if lead.cin_number and lead.mca_verified:
            score += 0.25
            
        # GST verification - 0.20
        if lead.gst_number and lead.gst_verified:
            score += 0.20
            
        # DPIIT recognition - 0.20
        if lead.dpiit_recognized:
            score += 0.20
            
        # MSME registration - 0.15
        if lead.udyam_number and lead.msme_verified:
            score += 0.15
            
        # GeM vendor - 0.10
        if lead.gem_vendor:
            score += 0.10
            
        # Active status - 0.10
        if lead.company_status == "Active":
            score += 0.10
            
        return min(1.0, score)
```

---

## Verification Checkpoints

### Checkpoint 4.1: DPIIT v2
- [ ] Extract 1000+ startups with full fields
- [ ] Founder contact info present
- [ ] GST/CIN numbers populated
- [ ] Stage classification accurate

### Checkpoint 4.2: MCA21
- [ ] Extract 500+ companies
- [ ] Director information present
- [ ] CIN parsing accuracy 100%
- [ ] Active status filter working

### Checkpoint 4.3: GeM
- [ ] Extract 500+ vendors
- [ ] Category filtering working
- [ ] Tender history populated

### Checkpoint 4.4: MSME
- [ ] Extract 1000+ MSMEs
- [ ] NIC code filtering working
- [ ] Owner contact info present

### Checkpoint 5.1: Cross-Reference
- [ ] 50%+ leads have CIN match
- [ ] 30%+ leads have GST match
- [ ] Verification score calculated correctly

---

## Testing

```python
# tests/collectors/test_government.py
import pytest
from backend.collectors.dpiit_v2 import DPIITv2Collector
from backend.collectors.mca21_v2 import MCA21Collector
from backend.collectors.gem import GeMCollector
from backend.collectors.msme import MSMECollector

@pytest.mark.asyncio
async def test_dpiit_collection():
    collector = DPIITv2Collector()
    startups = await collector.collect()
    
    assert len(startups) > 0
    assert all(s.source == "dpiit_v2" for s in startups)
    assert all(s.raw_meta.get("cin") for s in startups)
    assert all(s.raw_meta.get("gst_number") for s in startups)

@pytest.mark.asyncio
async def test_mca21_collection():
    collector = MCA21Collector()
    companies = await collector.collect()
    
    assert len(companies) > 0
    assert all(c.source == "mca21" for c in companies)
    assert all(c.raw_meta.get("cin") for c in companies)

@pytest.mark.asyncio
async def test_govt_cross_reference():
    from backend.services.govt_cross_reference import GovtCrossReferenceService
    
    service = GovtCrossReferenceService()
    # Mock lead with partial data
    lead = Lead(cin_number="U74999MH2020PTC123456")
    
    enriched = await service.enrich_lead(lead)
    assert enriched.govt_verification_score > 0
```

---

*Phases 4-5 - Government API Collectors*
*Duration: Week 4-5*
*Estimated leads/day: 3,000+ (Govt sources)*
