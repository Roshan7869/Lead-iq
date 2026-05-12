# Phase 8: Pipeline Integration
> Duration: Week 8
> Priority: CRITICAL
> Dependencies: Phases 2-7
> Goal: Connect all collectors, scoring, and enrichment into unified pipeline

---

## Objective
Build the central nervous system that connects all components into a cohesive data flow.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Collectors                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │ Naukri  │ │Internsha│ │  DPIIT  │ │  MCA21  │ │  GeM    │    │
│  │         │ │   la    │ │         │ │         │ │         │    │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │
│       │           │           │           │           │          │
│       └───────────┴───────────┴───────────┴───────────┘          │
│                           │                                      │
│                           ▼                                      │
│              ┌──────────────────────┐                            │
│              │   REDIS STREAMS      │                            │
│              │                      │                            │
│              │ lead:collected       │                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   ENRICHMENT         │                            │
│              │   WORKERS            │                            │
│              │                      │                            │
│              │ • Email finder       │                            │
│              │ • Phone verify       │                            │
│              │ • Govt cross-ref     │                            │
│              │ • Company verify     │                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   DEDUPLICATION      │                            │
│              │                      │                            │
│              │ Content hash +       │                            │
│              │ Vector similarity      │                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   SCORING            │                            │
│              │   WORKERS            │                            │
│              │                      │                            │
│              │ GBM + LLM Hybrid     │                            │
│              │ Composite score      │                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   RANKING            │                            │
│              │                      │                            │
│              │ Hot / Warm / Cool / Cold                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   ROUTING            │                            │
│              │                      │                            │
│              │ → Immediate outreach │                            │
│              │ → Nurture sequence   │                            │
│              │ → Long-term nurture  │                            │
│              │ → Drip campaign      │                            │
│              └──────────┬───────────┘                            │
│                       │                                          │
│                       ▼                                          │
│              ┌──────────────────────┐                            │
│              │   DATABASE           │                            │
│              │                      │                            │
│              │ PostgreSQL +         │                            │
│              │ pgvector             │                            │
│              └──────────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### 8.1 Redis Stream Architecture

```python
# backend/shared/stream_v2.py
"""
Enhanced Redis Streams for multi-source pipeline
"""
import json
import redis.asyncio as redis
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

class RedisStreamManager:
    """Manage Redis streams for pipeline"""
    
    STREAMS = {
        # Collection streams
        'lead:govt_collected': {'ttl': 86400},      # 24 hours
        'lead:jobs_collected': {'ttl': 86400},       # 24 hours
        'lead:social_collected': {'ttl': 86400},    # 24 hours
        
        # Processing streams
        'lead:enrichment_pending': {'ttl': 3600},   # 1 hour
        'lead:scoring_pending': {'ttl': 3600},        # 1 hour
        'lead:ranking_pending': {'ttl': 3600},      # 1 hour
        'lead:routing_pending': {'ttl': 3600},       # 1 hour
        
        # Completed streams
        'lead:enriched': {'ttl': 604800},           # 7 days
        'lead:scored': {'ttl': 604800},             # 7 days
        'lead:ranked': {'ttl': 604800},             # 7 days
        'lead:routed': {'ttl': 604800},             # 7 days
        
        # Dead letter queue
        'lead:dlq': {'ttl': 2592000},              # 30 days
    }
    
    CONSUMER_GROUPS = {
        'enrichment_workers': ['lead:govt_collected', 'lead:jobs_collected', 'lead:social_collected'],
        'scoring_workers': ['lead:enriched'],
        'ranking_workers': ['lead:scored'],
        'routing_workers': ['lead:ranked'],
    }
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        
    async def connect(self):
        """Connect to Redis"""
        self.client = redis.from_url(self.redis_url)
        
        # Create consumer groups
        for group_name, streams in self.CONSUMER_GROUPS.items():
            for stream in streams:
                try:
                    await self.client.xgroup_create(
                        stream, 
                        group_name, 
                        id='0',  # Start from beginning
                        mkstream=True
                    )
                except redis.ResponseError as e:
                    if "already exists" not in str(e):
                        raise
                        
        logger.info("redis_streams_initialized")
        
    async def publish(self, stream: str, data: Dict) -> str:
        """Publish data to stream"""
        message_id = await self.client.xadd(
            stream,
            {'data': json.dumps(data)},
            approximate=True  # Faster, less precise
        )
        return message_id
        
    async def consume(self, stream: str, group: str, consumer: str, count: int = 10) -> List[Dict]:
        """Consume messages from stream"""
        messages = await self.client.xreadgroup(
            group,
            consumer,
            {stream: '>'},  # Only new messages
            count=count,
            block=5000  # 5 second timeout
        )
        
        results = []
        for stream_name, entries in messages:
            for message_id, fields in entries:
                data = json.loads(fields['data'])
                data['_message_id'] = message_id
                results.append(data)
                
        return results
        
    async def ack(self, stream: str, group: str, message_id: str):
        """Acknowledge message processing"""
        await self.client.xack(stream, group, message_id)
        
    async def get_pending(self, stream: str, group: str) -> List[Dict]:
        """Get pending (unacknowledged) messages"""
        pending = await self.client.xpending_range(
            stream,
            group,
            min='-',
            max='+',
            count=100
        )
        return pending
        
    async def move_to_dlq(self, stream: str, group: str, message_id: str, error: str):
        """Move failed message to dead letter queue"""
        # Get original message
        messages = await self.client.xrange(stream, min=message_id, max=message_id)
        if messages:
            data = json.loads(messages[0][1]['data'])
            data['_original_stream'] = stream
            data['_error'] = error
            data['_dlq_timestamp'] = datetime.now().isoformat()
            
            # Add to DLQ
            await self.publish('lead:dlq', data)
            
            # Ack original
            await self.ack(stream, group, message_id)
            
            logger.warning("message_moved_to_dlq",
                        stream=stream,
                        message_id=message_id,
                        error=error)
```

### 8.2 Pipeline Workers

```python
# backend/workers/pipeline_v2.py
"""
Pipeline workers for multi-source processing
"""
import asyncio
from typing import Dict
import structlog

from backend.shared.stream_v2 import RedisStreamManager
from backend.services.enrichment import EnrichmentService
from backend.ml.composite_scorer import CompositeScorer
from backend.services.routing import RoutingService

logger = structlog.get_logger()

class EnrichmentWorker:
    """Worker for enriching collected leads"""
    
    def __init__(self, stream_manager: RedisStreamManager, enrichment: EnrichmentService):
        self.stream = stream_manager
        self.enrichment = enrichment
        self.group = 'enrichment_workers'
        
    async def run(self):
        """Run enrichment worker loop"""
        while True:
            try:
                # Read from all collection streams
                for stream in ['lead:govt_collected', 'lead:jobs_collected', 'lead:social_collected']:
                    messages = await self.stream.consume(stream, self.group, 'worker-1', count=100)
                    
                    for message in messages:
                        try:
                            # Enrich lead
                            enriched = await self.enrichment.enrich(message)
                            
                            # Publish to enriched stream
                            await self.stream.publish('lead:enriched', enriched)
                            
                            # Ack original
                            await self.stream.ack(stream, self.group, message['_message_id'])
                            
                        except Exception as e:
                            logger.error("enrichment_failed", error=str(e))
                            await self.stream.move_to_dlq(stream, self.group, message['_message_id'], str(e))
                            
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("enrichment_worker_error", error=str(e))
                await asyncio.sleep(5)

class ScoringWorker:
    """Worker for scoring enriched leads"""
    
    def __init__(self, stream_manager: RedisStreamManager, scorer: CompositeScorer):
        self.stream = stream_manager
        self.scorer = scorer
        self.group = 'scoring_workers'
        
    async def run(self):
        """Run scoring worker loop"""
        while True:
            try:
                messages = await self.stream.consume('lead:enriched', self.group, 'worker-1', count=50)
                
                for message in messages:
                    try:
                        # Score lead
                        result = await self.scorer.score(message)
                        
                        # Add scoring result to message
                        message['scoring'] = {
                            'final_score': result.final_score,
                            'band': result.band,
                            'component_scores': result.component_scores,
                            'confidence': result.confidence,
                            'recommended_action': result.recommended_action,
                        }
                        
                        # Publish to scored stream
                        await self.stream.publish('lead:scored', message)
                        
                        # Ack
                        await self.stream.ack('lead:enriched', self.group, message['_message_id'])
                        
                    except Exception as e:
                        logger.error("scoring_failed", error=str(e))
                        await self.stream.move_to_dlq('lead:enriched', self.group, message['_message_id'], str(e))
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("scoring_worker_error", error=str(e))
                await asyncio.sleep(5)

class RoutingWorker:
    """Worker for routing scored leads"""
    
    def __init__(self, stream_manager: RedisStreamManager, router: RoutingService):
        self.stream = stream_manager
        self.router = router
        self.group = 'routing_workers'
        
    async def run(self):
        """Run routing worker loop"""
        while True:
            try:
                messages = await self.stream.consume('lead:scored', self.group, 'worker-1', count=50)
                
                for message in messages:
                    try:
                        # Route lead
                        route = self.router.route(message)
                        
                        message['routing'] = {
                            'action': route.action,
                            'priority': route.priority,
                            'assigned_to': route.assigned_to,
                            'due_date': route.due_date.isoformat() if route.due_date else None,
                        }
                        
                        # Publish to routed stream
                        await self.stream.publish('lead:routed', message)
                        
                        # Save to database
                        await self._save_to_database(message)
                        
                        # Ack
                        await self.stream.ack('lead:scored', self.group, message['_message_id'])
                        
                    except Exception as e:
                        logger.error("routing_failed", error=str(e))
                        await self.stream.move_to_dlq('lead:scored', self.group, message['_message_id'], str(e))
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("routing_worker_error", error=str(e))
                await asyncio.sleep(5)
                
    async def _save_to_database(self, message: Dict):
        """Save routed lead to PostgreSQL"""
        from backend.shared.repository import LeadRepository
        
        repo = LeadRepository()
        await repo.save_lead(message)
```

### 8.3 API Endpoints

```python
# backend/api/routes/collection.py
"""
Collection API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/collect", tags=["collection"])

class CollectionRequest(BaseModel):
    source: str
    keywords: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    max_results: Optional[int] = 1000

class CollectionResponse(BaseModel):
    status: str
    job_id: str
    message: str

@router.post("/naukri")
async def collect_naukri(request: CollectionRequest, background: BackgroundTasks):
    """Trigger Naukri collection"""
    from backend.workers.actors import NaukriActor
    
    job_id = await NaukriActor().enqueue(
        keywords=request.keywords,
        locations=request.locations,
        max_results=request.max_results
    )
    
    return CollectionResponse(
        status="queued",
        job_id=job_id,
        message="Naukri collection started"
    )

@router.post("/internshala")
async def collect_internshala(request: CollectionRequest, background: BackgroundTasks):
    """Trigger Internshala collection"""
    from backend.workers.actors import InternshalaActor
    
    job_id = await InternshalaActor().enqueue(
        categories=request.keywords,
        max_results=request.max_results
    )
    
    return CollectionResponse(
        status="queued",
        job_id=job_id,
        message="Internshala collection started"
    )

@router.post("/gem")
async def collect_gem(request: CollectionRequest, background: BackgroundTasks):
    """Trigger GeM collection"""
    from backend.workers.actors import GeMActor
    
    job_id = await GeMActor().enqueue(
        categories=request.keywords,
        max_results=request.max_results
    )
    
    return CollectionResponse(
        status="queued",
        job_id=job_id,
        message="GeM collection started"
    )

@router.post("/all")
async def collect_all(background: BackgroundTasks):
    """Trigger collection from all sources"""
    sources = ['naukri', 'internshala', 'linkedin', 'dpiit', 'mca21', 'gem', 'msme']
    
    job_ids = []
    for source in sources:
        # Enqueue each source
        job_id = await enqueue_source(source)
        job_ids.append(job_id)
        
    return {
        "status": "queued",
        "sources": sources,
        "job_ids": job_ids,
        "message": f"Collection started for {len(sources)} sources"
    }
```

```python
# backend/api/routes/leads_v2.py
"""
Enhanced leads API endpoints
"""
from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/leads", tags=["leads"])

@router.get("/government")
async def get_government_leads(
    source: Optional[List[str]] = Query(None),
    state: Optional[str] = None,
    sector: Optional[str] = None,
    band: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
):
    """Get government-sourced leads"""
    from backend.shared.repository import LeadRepository
    
    repo = LeadRepository()
    leads = await repo.get_leads(
        sources=source or ['dpiit', 'mca21', 'gem', 'msme'],
        state=state,
        sector=sector,
        band=band,
        page=page,
        page_size=page_size
    )
    
    return {
        "total": leads.total,
        "page": page,
        "page_size": page_size,
        "leads": leads.items
    }

@router.get("/jobs")
async def get_job_leads(
    source: Optional[List[str]] = Query(None),
    skills: Optional[List[str]] = Query(None),
    experience: Optional[str] = None,
    work_mode: Optional[str] = None,
    salary_min: Optional[int] = None,
    band: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
):
    """Get job-sourced leads"""
    from backend.shared.repository import LeadRepository
    
    repo = LeadRepository()
    leads = await repo.get_leads(
        sources=source or ['naukri', 'internshala', 'linkedin', 'indeed'],
        skills=skills,
        experience=experience,
        work_mode=work_mode,
        salary_min=salary_min,
        band=band,
        page=page,
        page_size=page_size
    )
    
    return {
        "total": leads.total,
        "page": page,
        "page_size": page_size,
        "leads": leads.items
    }

@router.post("/scoring/batch")
async def batch_score_leads(lead_ids: List[str], force_recalculate: bool = False):
    """Batch re-score leads"""
    from backend.ml.composite_scorer import CompositeScorer
    
    scorer = CompositeScorer()
    results = []
    
    for lead_id in lead_ids:
        lead = await LeadRepository().get_by_id(lead_id)
        if lead:
            score = await scorer.score(lead)
            results.append({
                "lead_id": lead_id,
                "score": score.final_score,
                "band": score.band
            })
            
    return {
        "processed": len(results),
        "results": results
    }
```

---

## Verification Checkpoints

### Checkpoint 8.1: Redis Streams
- [ ] All 12 streams created
- [ ] Consumer groups initialized
- [ ] Message flow working end-to-end
- [ ] DLQ capturing failures

### Checkpoint 8.2: Workers
- [ ] Enrichment worker processing
- [ ] Scoring worker processing
- [ ] Routing worker processing
- [ ] Workers handling 100+ messages/minute

### Checkpoint 8.3: API Endpoints
- [ ] All collection endpoints responding
- [ ] Lead filtering working
- [ ] Batch scoring working
- [ ] Pagination working

---

*Phase 8 - Pipeline Integration*
*Duration: Week 8*
*Critical path: Yes*
