# Phases 9-10: Performance & Quality
> Duration: Week 9-10
> Priority: HIGH
> Dependencies: Phase 8
> Goal: Scale to 25K+ leads/day with >90% accuracy

---

## Phase 9: Performance Optimization

### Objective
Scale pipeline to handle 25,000+ leads/day with <5 minute latency.

### 9.1 Async Batch Processing

```python
# backend/services/batch_processor.py
"""
Batch processing for high-volume lead ingestion
"""
import asyncio
from typing import List, Dict, Callable
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class BatchConfig:
    batch_size: int = 100
    max_concurrent: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3

class BatchProcessor:
    """Process leads in batches with concurrency control"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        
    async def process_batch(self, leads: List[Dict], processor: Callable) -> List[Dict]:
        """Process batch of leads with controlled concurrency"""
        
        # Split into chunks
        chunks = [
            leads[i:i + self.config.batch_size]
            for i in range(0, len(leads), self.config.batch_size)
        ]
        
        # Process chunks in parallel
        tasks = [
            self._process_chunk(chunk, processor)
            for chunk in chunks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter errors
        processed = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("batch_chunk_failed", error=str(result))
            else:
                processed.extend(result)
                
        return processed
        
    async def _process_chunk(self, chunk: List[Dict], processor: Callable) -> List[Dict]:
        """Process a single chunk with semaphore"""
        async with self.semaphore:
            results = []
            for lead in chunk:
                try:
                    result = await processor(lead)
                    results.append(result)
                except Exception as e:
                    logger.warning("lead_processing_failed",
                                 lead_id=lead.get('id'),
                                 error=str(e))
            return results
```

### 9.2 Connection Pooling

```python
# backend/services/connection_pool.py
"""
Database and HTTP connection pooling
"""
import asyncpg
import httpx
from typing import Dict

class ConnectionPoolManager:
    """Manage connection pools for databases and HTTP"""
    
    def __init__(self):
        self.db_pools: Dict[str, asyncpg.Pool] = {}
        self.http_clients: Dict[str, httpx.AsyncClient] = {}
        
    async def create_db_pool(self, name: str, dsn: str, min_size: int = 5, max_size: int = 20):
        """Create PostgreSQL connection pool"""
        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
            server_settings={
                'jit': 'off',
                'application_name': 'leadiq'
            }
        )
        self.db_pools[name] = pool
        return pool
        
    async def get_db_pool(self, name: str) -> asyncpg.Pool:
        """Get database pool"""
        return self.db_pools[name]
        
    def create_http_client(self, name: str, limits: httpx.Limits = None):
        """Create HTTP client with connection pooling"""
        client = httpx.AsyncClient(
            limits=limits or httpx.Limits(max_keepalive_connections=20, max_connections=100),
            timeout=httpx.Timeout(30.0, connect=5.0),
            http2=True  # Enable HTTP/2 for multiplexing
        )
        self.http_clients[name] = client
        return client
        
    async def close_all(self):
        """Close all connections"""
        for pool in self.db_pools.values():
            await pool.close()
        for client in self.http_clients.values():
            await client.aclose()
```

### 9.3 Caching Layer

```python
# backend/services/cache_manager.py
"""
Multi-tier caching for lead data
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
import structlog

logger = structlog.get_logger()

class CacheManager:
    """Manage caching for frequently accessed data"""
    
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
        
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache with TTL"""
        await self.client.setex(
            key,
            ttl,
            json.dumps(value)
        )
        
    async def get_or_compute(self, key: str, compute_func, ttl: int = 3600):
        """Get from cache or compute and store"""
        cached = await self.get(key)
        if cached is not None:
            return cached
            
        value = await compute_func()
        await self.set(key, value, ttl)
        return value
        
    async def invalidate(self, pattern: str):
        """Invalidate cache by pattern"""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
            
    async def get_company_cache(self, company_name: str) -> Optional[Dict]:
        """Get cached company data"""
        return await self.get(f"company:{company_name}")
        
    async def set_company_cache(self, company_name: str, data: Dict, ttl: int = 86400):
        """Cache company data for 24 hours"""
        await self.set(f"company:{company_name}", data, ttl)
```

### 9.4 Circuit Breaker

```python
# backend/services/circuit_breaker.py
"""
Circuit breaker pattern for external service calls
"""
import asyncio
from enum import Enum
from typing import Callable
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failure threshold reached
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    async def call(self, func: Callable, *args, **kwargs):
        """Call function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("circuit_breaker_half_open", name=self.name)
            else:
                raise CircuitBreakerOpen(f"Circuit {self.name} is OPEN")
                
        elif self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpen(f"Circuit {self.name} half-open limit reached")
            self.half_open_calls += 1
            
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
            
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self._reset()
        else:
            self.failure_count = 0
            
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_breaker_opened",
                        name=self.name,
                        failures=self.failure_count)
                        
    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has passed"""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        
    def _reset(self):
        """Reset circuit breaker to closed"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        logger.info("circuit_breaker_closed", name=self.name)

class CircuitBreakerOpen(Exception):
    pass
```

---

## Phase 10: Data Quality

### Objective
Ensure >90% data accuracy with automated validation and anomaly detection.

### 10.1 Data Validation Pipeline

```python
# backend/services/data_validator.py
"""
Automated data validation for lead quality
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, validator
import structlog

logger = structlog.get_logger()

class LeadSchema(BaseModel):
    """Pydantic schema for lead validation"""
    
    source: str
    external_id: str
    title: str
    body: Optional[str] = ""
    author: Optional[str] = ""
    
    # Company info
    company_name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    
    # Validation rules
    @validator('source')
    def validate_source(cls, v):
        valid_sources = [
            'naukri', 'internshala', 'linkedin', 'indeed', 'shine', 'monster',
            'freshersworld', 'hirist', 'cutshort', 'angellist', 'instahyre',
            'dpiit', 'mca21', 'gem', 'msme', 'reddit', 'hn', 'github',
            'stackoverflow', 'twitter', 'telegram', 'producthunt', 'rss'
        ]
        if v not in valid_sources:
            raise ValueError(f"Invalid source: {v}")
        return v
        
    @validator('title')
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError("Title too short")
        if len(v) > 500:
            raise ValueError("Title too long")
        return v.strip()
        
    @validator('external_id')
    def validate_external_id(cls, v):
        if not v or v == 'unknown':
            raise ValueError("External ID required")
        return v

class DataValidator:
    """Validate lead data quality"""
    
    def __init__(self):
        self.schema = LeadSchema
        
    async def validate(self, lead: Dict) -> Dict:
        """Validate single lead"""
        errors = []
        warnings = []
        
        # Schema validation
        try:
            validated = self.schema(**lead)
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
            
        # Content quality checks
        if lead.get('body') and len(lead['body']) < 20:
            warnings.append("Body content too short")
            
        # Contact info checks
        has_contact = bool(
            lead.get('raw_meta', {}).get('email') or
            lead.get('raw_meta', {}).get('website') or
            lead.get('raw_meta', {}).get('company_website')
        )
        if not has_contact:
            warnings.append("No contact information found")
            
        # Source-specific checks
        source = lead.get('source')
        if source in ['naukri', 'internshala', 'linkedin']:
            if not lead.get('raw_meta', {}).get('company_name'):
                errors.append("Job lead missing company name")
                
        elif source in ['dpiit', 'mca21', 'gem']:
            if not lead.get('raw_meta', {}).get('company_name'):
                errors.append("Government lead missing company name")
                
        # Cross-field validation
        salary_min = lead.get('raw_meta', {}).get('salary_min')
        salary_max = lead.get('raw_meta', {}).get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            errors.append("Salary min > salary max")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    async def validate_batch(self, leads: List[Dict]) -> Dict:
        """Validate batch of leads"""
        results = []
        for lead in leads:
            result = await self.validate(lead)
            results.append({
                'lead_id': lead.get('id', 'unknown'),
                **result
            })
            
        valid_count = sum(1 for r in results if r['valid'])
        
        return {
            'total': len(leads),
            'valid': valid_count,
            'invalid': len(leads) - valid_count,
            'accuracy': (valid_count / len(leads)) * 100 if leads else 0,
            'details': results
        }
```

### 10.2 Anomaly Detection

```python
# backend/services/anomaly_detector.py
"""
Anomaly detection for lead data quality
"""
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class AnomalyDetector:
    """Detect anomalies in lead data"""
    
    def __init__(self):
        self.baselines = {}
        
    async def detect(self, leads: List[Dict]) -> List[Dict]:
        """Detect anomalies in lead batch"""
        anomalies = []
        
        # Check volume anomalies
        volume_anomaly = self._check_volume(leads)
        if volume_anomaly:
            anomalies.append(volume_anomaly)
            
        # Check source distribution anomalies
        source_anomaly = self._check_source_distribution(leads)
        if source_anomaly:
            anomalies.append(source_anomaly)
            
        # Check field completeness anomalies
        completeness_anomaly = self._check_completeness(leads)
        if completeness_anomaly:
            anomalies.append(completeness_anomaly)
            
        # Check duplicate anomalies
        duplicate_anomaly = self._check_duplicates(leads)
        if duplicate_anomaly:
            anomalies.append(duplicate_anomaly)
            
        return anomalies
        
    def _check_volume(self, leads: List[Dict]) -> Optional[Dict]:
        """Check for unusual volume"""
        count = len(leads)
        baseline = self.baselines.get('volume', 1000)
        
        if count > baseline * 5:  # 5x normal volume
            return {
                'type': 'volume_spike',
                'severity': 'high',
                'details': f"Volume {count} is {count/baseline:.1f}x normal",
                'action': 'investigate_source'
            }
        elif count < baseline * 0.1:  # <10% normal volume
            return {
                'type': 'volume_drop',
                'severity': 'high',
                'details': f"Volume {count} is {count/baseline:.1%} of normal",
                'action': 'check_collectors'
            }
        return None
        
    def _check_source_distribution(self, leads: List[Dict]) -> Optional[Dict]:
        """Check for unusual source distribution"""
        sources = {}
        for lead in leads:
            source = lead.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            
        # Check if one source dominates (>80%)
        total = len(leads)
        for source, count in sources.items():
            if count / total > 0.8:
                return {
                    'type': 'source_dominance',
                    'severity': 'medium',
                    'details': f"{source} is {count/total:.1%} of leads",
                    'action': 'verify_diversification'
                }
        return None
        
    def _check_completeness(self, leads: List[Dict]) -> Optional[Dict]:
        """Check for field completeness issues"""
        total = len(leads)
        missing_company = sum(1 for l in leads if not l.get('raw_meta', {}).get('company_name'))
        
        if missing_company / total > 0.3:  # >30% missing company
            return {
                'type': 'low_completeness',
                'severity': 'medium',
                'details': f"{missing_company/total:.1%} missing company name",
                'action': 'improve_parsing'
            }
        return None
        
    def _check_duplicates(self, leads: List[Dict]) -> Optional[Dict]:
        """Check for duplicate anomalies"""
        hashes = [l.get('content_hash') for l in leads]
        unique = len(set(hashes))
        total = len(hashes)
        
        if unique / total < 0.8:  # >20% duplicates
            return {
                'type': 'high_duplicates',
                'severity': 'high',
                'details': f"{1 - unique/total:.1%} duplicate rate",
                'action': 'tune_dedup'
            }
        return None
```

---

## Verification Checkpoints

### Phase 9 Checkpoints
- [ ] Batch processing: 1000+ leads/minute
- [ ] Connection pooling: <50ms query time
- [ ] Cache hit rate: >70%
- [ ] Circuit breaker: trips correctly
- [ ] Memory usage: <2GB

### Phase 10 Checkpoints
- [ ] Schema validation: >95% pass
- [ ] Anomaly detection: catches issues
- [ ] Data accuracy: >90%
- [ ] Duplicate rate: <5%
- [ ] Alerting: working for all thresholds

---

*Phases 9-10 - Performance & Quality*
*Duration: Week 9-10*
*Target: 25K+ leads/day, >90% accuracy*
