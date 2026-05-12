# Phases 11-12: Testing & Deployment
> Duration: Week 11-12
> Priority: CRITICAL
> Dependencies: Phases 9-10
> Goal: Production-ready deployment with comprehensive testing

---

## Phase 11: Testing

### Objective
Achieve 80%+ test coverage with comprehensive unit, integration, and load tests.

### 11.1 Test Structure

```
tests/
├── unit/
│   ├── collectors/
│   │   ├── test_naukri.py
│   │   ├── test_internshala.py
│   │   ├── test_dpiit.py
│   │   ├── test_mca21.py
│   │   ├── test_gem.py
│   │   ├── test_msme.py
│   │   └── test_base_collector.py
│   ├── services/
│   │   ├── test_enrichment.py
│   │   ├── test_scoring.py
│   │   ├── test_dedup.py
│   │   ├── test_validation.py
│   │   └── test_routing.py
│   └── utils/
│       ├── test_scraping_utils.py
│       ├── test_proxy_manager.py
│       └── test_retry_handler.py
├── integration/
│   ├── test_pipeline.py
│   ├── test_api_endpoints.py
│   ├── test_redis_streams.py
│   └── test_database.py
├── load/
│   ├── test_collection_rate.py
│   ├── test_api_throughput.py
│   └── test_pipeline_capacity.py
└── e2e/
    ├── test_full_flow.py
    └── test_production_scenarios.py
```

### 11.2 Unit Tests

```python
# tests/unit/collectors/test_naukri.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.collectors.naukri import NaukriCollector
from backend.collectors.base import RawPost

class TestNaukriCollector:
    """Unit tests for Naukri collector"""
    
    @pytest.fixture
    def collector(self):
        return NaukriCollector()
        
    @pytest.mark.asyncio
    async def test_collection_returns_posts(self, collector):
        """Test that collector returns RawPost objects"""
        # Mock the scraping methods
        with patch.object(collector, '_scrape_search', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = [
                RawPost(
                    source='naukri',
                    external_id='test-1',
                    url='https://naukri.com/job/1',
                    title='Software Engineer',
                    body='Job description',
                    author='TechCorp',
                    raw_meta={'company_name': 'TechCorp', 'salary_min': 500000}
                )
            ]
            
            collector.target_keywords = ['software engineer']
            collector.target_locations = ['bangalore']
            
            results = await collector.collect()
            
            assert len(results) > 0
            assert all(isinstance(r, RawPost) for r in results)
            assert all(r.source == 'naukri' for r in results)
            
    @pytest.mark.asyncio
    async def test_salary_parsing(self, collector):
        """Test salary string parsing"""
        test_cases = [
            ('₹5-10 LPA', 500000, 1000000),
            ('₹15 Lacs P.A.', 1500000, 1500000),
            ('Competitive', None, None),
            ('', None, None),
        ]
        
        for input_str, expected_min, expected_max in test_cases:
            min_val, max_val = collector._parse_salary(input_str)
            assert min_val == expected_min
            assert max_val == expected_max
            
    @pytest.mark.asyncio
    async def test_experience_parsing(self, collector):
        """Test experience string parsing"""
        test_cases = [
            ('0-2 years', 0, 2),
            ('5+ years', 5, 5),
            ('Fresher', 0, 0),
            ('', None, None),
        ]
        
        for input_str, expected_min, expected_max in test_cases:
            min_val, max_val = collector._parse_experience(input_str)
            assert min_val == expected_min
            assert max_val == expected_max
            
    @pytest.mark.asyncio
    async def test_handles_empty_results(self, collector):
        """Test handling of empty search results"""
        with patch.object(collector, '_scrape_search', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = []
            
            collector.target_keywords = ['nonexistentjob12345']
            collector.target_locations = ['nowhere']
            
            results = await collector.collect()
            assert len(results) == 0

# tests/unit/ml/test_scoring.py
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from backend.ml.scoring_model import GradientBoostingScorer
from backend.ml.composite_scorer import CompositeScorer

class TestGradientBoostingScorer:
    """Unit tests for GBM scoring"""
    
    @pytest.fixture
    def scorer(self):
        return GradientBoostingScorer()
        
    def test_feature_extraction(self, scorer):
        """Test feature extraction from lead"""
        lead = MagicMock()
        lead.source = 'naukri'
        lead.stage = 'new'
        lead.company_size = 'startup'
        lead.industry = 'saas'
        lead.location = 'bangalore'
        lead.gst_number = '29ABCDE1234F1Z5'
        lead.engagement_metrics = {'page_views': 10, 'email_opens': 2}
        lead.raw_meta = {'job_count': 5}
        
        features = scorer._extract_features(lead)
        
        assert 'source_encoded' in features
        assert 'govt_registered' in features
        assert features['govt_registered'] == 1
        assert features['page_views'] == 10
        
    def test_score_range(self, scorer):
        """Test that score is in valid range"""
        with patch.object(scorer, '_load_model'):
            scorer.model = MagicMock()
            scorer.model.predict_proba.return_value = np.array([[0.3, 0.7]])
            
            lead = MagicMock()
            score = scorer.predict(lead)
            
            assert 0 <= score <= 1

class TestCompositeScorer:
    """Unit tests for composite scoring"""
    
    @pytest.fixture
    def scorer(self):
        return CompositeScorer()
        
    @pytest.mark.asyncio
    async def test_all_components_run(self, scorer):
        """Test that all scoring components execute"""
        lead = MagicMock()
        lead.location = 'bangalore'
        
        with patch.object(scorer.gbm, 'predict', return_value=0.7), \
             patch.object(scorer.llm, 'analyze', return_value={'qualitative_score': 75}), \
             patch.object(scorer.rl, 'predict', return_value=0.6), \
             patch.object(scorer.uplift, 'compute', return_value=0.5), \
             patch.object(scorer.geo, 'adjust', return_value=0.8):
            
            result = await scorer.score(lead)
            
            assert result.final_score >= 0
            assert result.final_score <= 100
            assert result.band in ['hot', 'warm', 'cool', 'cold']
            assert 'gbm' in result.component_scores
            assert 'llm' in result.component_scores
```

### 11.3 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
import asyncio
from backend.workers.pipeline_v2 import EnrichmentWorker, ScoringWorker, RoutingWorker
from backend.shared.stream_v2 import RedisStreamManager
from backend.services.enrichment import EnrichmentService
from backend.ml.composite_scorer import CompositeScorer
from backend.services.routing import RoutingService

class TestPipelineIntegration:
    """Integration tests for full pipeline"""
    
    @pytest.fixture
    async def pipeline(self, redis_client):
        """Setup full pipeline"""
        stream_manager = RedisStreamManager(redis_client)
        await stream_manager.connect()
        
        enrichment = EnrichmentService()
        scorer = CompositeScorer()
        router = RoutingService()
        
        workers = {
            'enrichment': EnrichmentWorker(stream_manager, enrichment),
            'scoring': ScoringWorker(stream_manager, scorer),
            'routing': RoutingWorker(stream_manager, router),
        }
        
        return workers
        
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, pipeline):
        """Test complete pipeline flow"""
        # Create test lead
        test_lead = {
            'source': 'naukri',
            'external_id': 'test-123',
            'title': 'Software Engineer',
            'company_name': 'TestCorp',
            'industry': 'saas',
            'location': 'bangalore',
            'raw_meta': {'skills': ['python', 'react']}
        }
        
        # Publish to collection stream
        await pipeline['enrichment'].stream.publish('lead:jobs_collected', test_lead)
        
        # Run enrichment
        await asyncio.sleep(2)
        
        # Check enriched stream
        enriched = await pipeline['scoring'].stream.consume('lead:enriched', 'test_group', 'test_consumer', count=1)
        assert len(enriched) > 0
        
        # Run scoring
        await asyncio.sleep(2)
        
        # Check scored stream
        scored = await pipeline['routing'].stream.consume('lead:scored', 'test_group', 'test_consumer', count=1)
        assert len(scored) > 0
        assert 'scoring' in scored[0]
        assert 'final_score' in scored[0]['scoring']

# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
    def test_collect_naukri(self):
        """Test Naukri collection trigger"""
        response = client.post("/api/collect/naukri", json={
            "keywords": ["software engineer"],
            "locations": ["bangalore"],
            "max_results": 100
        })
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        
    def test_get_government_leads(self):
        """Test government leads endpoint"""
        response = client.get("/api/leads/government?source=dpiit&state=Karnataka")
        assert response.status_code == 200
        assert "leads" in response.json()
        
    def test_get_job_leads(self):
        """Test job leads endpoint"""
        response = client.get("/api/leads/jobs?skills=python&work_mode=remote")
        assert response.status_code == 200
        assert "leads" in response.json()
```

### 11.4 Load Tests

```python
# tests/load/test_collection_rate.py
import pytest
import asyncio
import time
from backend.collectors.naukri import NaukriCollector
from backend.collectors.internshala import InternshalaCollector

class TestCollectionLoad:
    """Load tests for collection rate"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_naukri_collection_rate(self):
        """Test Naukri collection rate"""
        collector = NaukriCollector()
        collector.target_keywords = ['software engineer']
        collector.target_locations = ['bangalore']
        collector.max_pages = 5
        
        start = time.time()
        results = await collector.collect()
        duration = time.time() - start
        
        rate = len(results) / duration
        print(f"Naukri collection rate: {rate:.1f} jobs/sec")
        
        # Should collect at least 100 jobs in <60 seconds
        assert len(results) >= 100
        assert duration < 60
        
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_parallel_collection(self):
        """Test parallel collection from multiple sources"""
        collectors = [
            NaukriCollector(),
            InternshalaCollector(),
        ]
        
        start = time.time()
        
        # Run in parallel
        results = await asyncio.gather(*[
            c.collect() for c in collectors
        ])
        
        duration = time.time() - start
        total = sum(len(r) for r in results)
        
        print(f"Parallel collection: {total} leads in {duration:.1f}s")
        
        assert total >= 200
        assert duration < 120

# tests/load/test_api_throughput.py
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestAPIThroughput:
    """Load tests for API throughput"""
    
    def test_api_throughput(self):
        """Test API throughput"""
        start = time.time()
        
        # Make 100 requests
        for i in range(100):
            response = client.get("/api/health")
            assert response.status_code == 200
            
        duration = time.time() - start
        throughput = 100 / duration
        
        print(f"API throughput: {throughput:.1f} req/sec")
        
        # Should handle >50 req/sec
        assert throughput > 50
```

### 11.5 Coverage Requirements

```ini
# .coveragerc
[run]
source = backend
branch = True
omit = 
    */tests/*
    */venv/*
    */migrations/*
    */__main__.py

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

fail_under = 80
```

---

## Phase 12: Deployment

### Objective
Production-ready deployment with monitoring, CI/CD, and documentation.

### 12.1 Docker Compose

```yaml
# infra/docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: infra/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://leadiq:password@postgres:5432/leadiq
      - REDIS_URL=redis://redis:6379
      - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    volumes:
      - proxy-pool:/app/proxies
      - models:/app/models
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker-enrichment:
    build:
      context: ..
      dockerfile: infra/Dockerfile.backend
    command: python -m backend.workers.enrichment_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://leadiq:password@postgres:5432/leadiq
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3

  worker-scoring:
    build:
      context: ..
      dockerfile: infra/Dockerfile.backend
    command: python -m backend.workers.scoring_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://leadiq:password@postgres:5432/leadiq
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2

  worker-routing:
    build:
      context: ..
      dockerfile: infra/Dockerfile.backend
    command: python -m backend.workers.routing_worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://leadiq:password@postgres:5432/leadiq
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=leadiq
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=leadiq
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    command: postgres -c shared_buffers=512MB -c effective_cache_size=1536MB

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  proxy-pool:
  models:
  redis-data:
  postgres-data:
  prometheus-data:
  grafana-data:
```

### 12.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: LeadIQ CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: leadiq_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
          
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
          
      - name: Run tests
        run: |
          cd backend
          pytest ../tests/ --cov=backend --cov-report=xml --cov-fail-under=80
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install linters
        run: |
          pip install black flake8 mypy
          
      - name: Check formatting
        run: black --check backend/
        
      - name: Run flake8
        run: flake8 backend/ --max-line-length=100
        
      - name: Type check
        run: mypy backend/ --ignore-missing-imports
        
  deploy:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        run: |
          echo "Deploying to production..."
          # Add actual deployment steps
```

### 12.3 Monitoring Setup

```python
# backend/services/monitoring.py
"""
Monitoring and alerting setup
"""
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Prometheus metrics
collectors = Counter('leadiq_collectors_total', 'Total collectors run', ['source', 'status'])
leads_collected = Counter('leadiq_leads_collected_total', 'Total leads collected', ['source'])
leads_scored = Counter('leadiq_leads_scored_total', 'Total leads scored', ['band'])
scoring_duration = Histogram('leadiq_scoring_duration_seconds', 'Scoring duration')
pipeline_latency = Histogram('leadiq_pipeline_latency_seconds', 'Pipeline latency')
active_workers = Gauge('leadiq_active_workers', 'Active worker count', ['type'])
queue_depth = Gauge('leadiq_queue_depth', 'Queue depth', ['queue'])

def init_monitoring():
    """Initialize monitoring"""
    # Start Prometheus metrics server
    start_http_server(9090)
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn="https://your-sentry-dsn",
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )
    
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

### 12.4 Documentation

```markdown
# LeadIQ Deployment Guide

## Prerequisites
- Docker 24+
- Docker Compose 2+
- 8GB RAM minimum
- 100GB disk space

## Quick Start
```bash
# Clone repository
git clone https://github.com/yourorg/leadiq.git
cd leadiq

# Start services
cd infra
docker compose up -d

# Verify health
curl http://localhost:8000/api/health
```

## Configuration
Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GEMINI_API_KEY`: For LLM scoring
- `PROXY_PROVIDER`: BrightData/ScrapingBee
- `PROXY_USERNAME`: Proxy credentials
- `PROXY_PASSWORD`: Proxy credentials

## Monitoring
- API: http://localhost:8000/api/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Troubleshooting
See docs/TROUBLESHOOTING.md
```

---

## Verification Checkpoints

### Phase 11 Checkpoints
- [ ] Unit tests: >80% coverage
- [ ] Integration tests: all passing
- [ ] Load tests: >1000 req/s
- [ ] E2E tests: full flow working
- [ ] Code review: approved

### Phase 12 Checkpoints
- [ ] Docker compose: all services running
- [ ] CI/CD: pipeline passing
- [ ] Monitoring: metrics flowing
- [ ] Documentation: complete
- [ ] Runbook: created
- [ ] Production: deployed

---

## Deployment Checklist

```
Pre-deployment:
☐ All tests passing
☐ Code reviewed
☐ Security scan passed
☐ Performance benchmarks met
☐ Documentation complete
☐ Runbook created
☐ Rollback plan ready

Deployment:
☐ Database migrations applied
☐ Services deployed
☐ Health checks passing
☐ Monitoring active
☐ Alerts configured

Post-deployment:
☐ Smoke tests passing
☐ Metrics flowing
☐ Logs visible
☐ Alerts working
☐ Team notified
```

---

*Phases 11-12 - Testing & Deployment*
*Duration: Week 11-12*
*Target: Production-ready*
