# Execution Orchestration Plan
> Adaptive-Imagining-Cat Execution DAG
> Complete orchestration of all phases with dependencies
> Date: 2026-05-11

---

## Execution DAG

```
Phase 0: State Preservation
├── Save all research data to plans/
├── Snapshot current codebase
└── Backup database schema

Phase 1: Foundation [Week 1]
├── Task 1.1: Install dependencies
├── Task 1.2: Create scraping utilities
├── Task 1.3: Create proxy manager
├── Task 1.4: Create stealth session
├── Task 1.5: Create retry handler
└── Verification: All tests pass

Phase 2: Naukri Collector [Week 2]
├── DEPENDS ON: Phase 1
├── Task 2.1: Analyze API endpoints
├── Task 2.2: Implement API interception
├── Task 2.3: Implement HTML fallback
├── Task 2.4: Create worker actor
└── Verification: 1000+ jobs extracted

Phase 3: Internshala Collector [Week 2-3]
├── DEPENDS ON: Phase 1
├── Task 3.1: Build direct scraper
├── Task 3.2: Parse internship cards
├── Task 3.3: Create worker actor
└── Verification: 500+ internships extracted

Phase 4: Government APIs [Week 4-5]
├── DEPENDS ON: Phase 1
├── Task 4.1: DPIIT v2 enhanced
├── Task 4.2: MCA21 integration
├── Task 4.3: GeM portal vendor scraper
├── Task 4.4: MSME Udyam collector
├── Task 4.5: API Setu client
├── Task 4.6: Cross-reference pipeline
└── Verification: 3000+ govt leads/day

Phase 5: LinkedIn + Others [Week 5]
├── DEPENDS ON: Phase 1
├── Task 5.1: LinkedIn Jobs API
├── Task 5.2: Indeed India
├── Task 5.3: Shine.com
└── Verification: Additional 5000+ leads/day

Phase 6: GBM Scoring [Week 6]
├── DEPENDS ON: Phase 2,3,4,5
├── Task 6.1: Feature engineering
├── Task 6.2: Model training
├── Task 6.3: Model evaluation
└── Verification: ROC AUC > 0.85

Phase 7: LLM Scoring [Week 7]
├── DEPENDS ON: Phase 6
├── Task 7.1: Build qualitative analyzer
├── Task 7.2: Implement prompt templates
├── Task 7.3: Composite scorer
└── Verification: All models run

Phase 8: Pipeline Integration [Week 8]
├── DEPENDS ON: Phase 2-7
├── Task 8.1: Redis streams
├── Task 8.2: API endpoints
├── Task 8.3: Workers orchestration
└── Verification: End-to-end flow

Phase 9: Performance [Week 9]
├── DEPENDS ON: Phase 8
├── Task 9.1: Async batch processing
├── Task 9.2: Connection pooling
├── Task 9.3: Caching layer
├── Task 9.4: Circuit breaker
└── Verification: 25K+ leads/day

Phase 10: Quality [Week 10]
├── DEPENDS ON: Phase 8
├── Task 10.1: Data validation
├── Task 10.2: Cross-reference verification
├── Task 10.3: Anomaly detection
└── Verification: 90%+ accuracy

Phase 11: Testing [Week 11]
├── DEPENDS ON: Phase 9,10
├── Task 11.1: Unit tests (80%+ coverage)
├── Task 11.2: Integration tests
├── Task 11.3: Load tests
└── Verification: All tests pass

Phase 12: Deployment [Week 12]
├── DEPENDS ON: Phase 11
├── Task 12.1: Docker compose
├── Task 12.2: CI/CD pipeline
├── Task 12.3: Monitoring setup
├── Task 12.4: Documentation
└── Verification: Production ready
```

---

## Parallel Execution Plan

```python
# execution_plan.py
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class PhaseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Phase:
    id: str
    name: str
    description: str
    duration_weeks: int
    dependencies: List[str]
    tasks: List[str]
    verification: List[str]
    status: PhaseStatus
    assigned_to: str = None
    start_date: str = None
    end_date: str = None

class ExecutionOrchestrator:
    """Orchestrate phase execution with dependency management"""
    
    def __init__(self):
        self.phases = self._define_phases()
        self.execution_order = []
        
    def _define_phases(self) -> Dict[str, Phase]:
        """Define all phases"""
        return {
            "phase_0": Phase(
                id="phase_0",
                name="State Preservation",
                description="Save research and snapshot current state",
                duration_weeks=0,
                dependencies=[],
                tasks=["Save research data", "Snapshot codebase", "Backup schema"],
                verification=["All data saved to plans/"],
                status=PhaseStatus.COMPLETED
            ),
            "phase_1": Phase(
                id="phase_1",
                name="Foundation",
                description="Build scraping infrastructure",
                duration_weeks=1,
                dependencies=["phase_0"],
                tasks=[
                    "Install dependencies (playwright, curl_cffi, etc.)",
                    "Create scraping utilities",
                    "Create proxy manager",
                    "Create stealth session",
                    "Create retry handler",
                    "Update compliance registry"
                ],
                verification=[
                    "Bot detection pass rate > 95%",
                    "Proxy rotation > 90%",
                    "Retry success > 95%"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_2": Phase(
                id="phase_2",
                name="Naukri Collector",
                description="Deploy Naukri.com scraper",
                duration_weeks=1,
                dependencies=["phase_1"],
                tasks=[
                    "Analyze API endpoints",
                    "Implement API interception",
                    "Implement HTML fallback",
                    "Create worker actor",
                    "Add compliance entry"
                ],
                verification=[
                    "1000+ jobs extracted",
                    "Salary parsing > 90%",
                    "No IP blocks in 100 requests"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_3": Phase(
                id="phase_3",
                name="Internshala Collector",
                description="Deploy Internshala scraper",
                duration_weeks=1,
                dependencies=["phase_1"],
                tasks=[
                    "Build direct scraper",
                    "Parse internship cards",
                    "Create worker actor",
                    "Add compliance entry"
                ],
                verification=[
                    "500+ internships extracted",
                    "Stipend parsing > 90%",
                    "Pagination working"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_4": Phase(
                id="phase_4",
                name="Government APIs",
                description="Integrate government data sources",
                duration_weeks=2,
                dependencies=["phase_1"],
                tasks=[
                    "DPIIT v2 enhanced collector",
                    "MCA21 integration",
                    "GeM portal vendor scraper",
                    "MSME Udyam collector",
                    "API Setu client",
                    "Cross-reference pipeline"
                ],
                verification=[
                    "DPIIT: 1000+ startups",
                    "MCA21: 500+ companies",
                    "GeM: 500+ vendors",
                    "MSME: 1000+ registrations"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_5": Phase(
                id="phase_5",
                name="LinkedIn + Others",
                description="Additional job platforms",
                duration_weeks=1,
                dependencies=["phase_1"],
                tasks=[
                    "LinkedIn Jobs API",
                    "Indeed India scraper",
                    "Shine.com scraper",
                    "Monster India scraper"
                ],
                verification=[
                    "Additional 5000+ leads/day",
                    "All platforms working"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_6": Phase(
                id="phase_6",
                name="GBM Scoring",
                description="Gradient Boosting scoring model",
                duration_weeks=1,
                dependencies=["phase_2", "phase_3", "phase_4", "phase_5"],
                tasks=[
                    "Feature engineering pipeline",
                    "Model training",
                    "Model evaluation",
                    "Feature importance analysis",
                    "Model persistence"
                ],
                verification=[
                    "ROC AUC > 0.85",
                    "CV mean > 0.80",
                    "Feature importance extracted"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_7": Phase(
                id="phase_7",
                name="LLM Scoring",
                description="Hybrid LLM qualitative analysis",
                duration_weeks=1,
                dependencies=["phase_6"],
                tasks=[
                    "Build qualitative analyzer",
                    "Implement prompt templates",
                    "Build composite scorer",
                    "Tune weights"
                ],
                verification=[
                    "Qualitative score 0-100",
                    "All 5 models run",
                    "Composite score computed"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_8": Phase(
                id="phase_8",
                name="Pipeline Integration",
                description="Connect all components",
                duration_weeks=1,
                dependencies=["phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7"],
                tasks=[
                    "Redis streams architecture",
                    "API endpoints",
                    "Workers orchestration",
                    "Deduplication logic",
                    "Enrichment pipeline"
                ],
                verification=[
                    "End-to-end flow working",
                    "All API endpoints responding",
                    "Workers processing"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_9": Phase(
                id="phase_9",
                name="Performance Optimization",
                description="Scale to 25K+ leads/day",
                duration_weeks=1,
                dependencies=["phase_8"],
                tasks=[
                    "Async batch processing",
                    "Connection pooling",
                    "Caching layer",
                    "Circuit breaker",
                    "Horizontal scaling"
                ],
                verification=[
                    "25K+ leads/day",
                    "Pipeline latency < 5min",
                    "Memory usage < 2GB"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_10": Phase(
                id="phase_10",
                name="Data Quality",
                description="Ensure 90%+ accuracy",
                duration_weeks=1,
                dependencies=["phase_8"],
                tasks=[
                    "Data validation pipeline",
                    "Cross-reference verification",
                    "Anomaly detection",
                    "Freshness monitoring",
                    "Coverage analysis"
                ],
                verification=[
                    "90%+ data accuracy",
                    "Anomaly detection working",
                    "Coverage > 95%"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_11": Phase(
                id="phase_11",
                name="Testing",
                description="Comprehensive test coverage",
                duration_weeks=1,
                dependencies=["phase_9", "phase_10"],
                tasks=[
                    "Unit tests (80%+ coverage)",
                    "Integration tests",
                    "Load tests",
                    "E2E tests"
                ],
                verification=[
                    "80%+ test coverage",
                    "All tests passing",
                    "Load test > 1000 req/s"
                ],
                status=PhaseStatus.PENDING
            ),
            "phase_12": Phase(
                id="phase_12",
                name="Deployment",
                description="Production deployment",
                duration_weeks=1,
                dependencies=["phase_11"],
                tasks=[
                    "Docker compose setup",
                    "CI/CD pipeline",
                    "Monitoring setup",
                    "Documentation",
                    "Runbook creation"
                ],
                verification=[
                    "Production ready",
                    "Monitoring active",
                    "Documentation complete"
                ],
                status=PhaseStatus.PENDING
            ),
        }
        
    def get_execution_order(self) -> List[str]:
        """Determine execution order based on dependencies"""
        
        # Topological sort
        visited = set()
        order = []
        
        def visit(phase_id):
            if phase_id in visited:
                return
            visited.add(phase_id)
            
            phase = self.phases[phase_id]
            for dep in phase.dependencies:
                visit(dep)
                
            order.append(phase_id)
            
        for phase_id in self.phases:
            visit(phase_id)
            
        return order
        
    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of phases that can run in parallel"""
        
        groups = []
        completed = set()
        
        while len(completed) < len(self.phases):
            # Find phases whose dependencies are all completed
            parallel = []
            for phase_id, phase in self.phases.items():
                if phase_id not in completed:
                    if all(dep in completed for dep in phase.dependencies):
                        parallel.append(phase_id)
                        
            if parallel:
                groups.append(parallel)
                completed.update(parallel)
            else:
                break
                
        return groups
        
    def get_critical_path(self) -> List[str]:
        """Get critical path (longest dependency chain)"""
        
        def path_length(phase_id):
            phase = self.phases[phase_id]
            if not phase.dependencies:
                return phase.duration_weeks
            return phase.duration_weeks + max(
                path_length(dep) for dep in phase.dependencies
            )
            
        # Find phase with longest path
        critical = max(self.phases.keys(), key=path_length)
        
        # Reconstruct path
        path = [critical]
        while self.phases[path[-1]].dependencies:
            next_phase = max(
                self.phases[path[-1]].dependencies,
                key=path_length
            )
            path.append(next_phase)
            
        return list(reversed(path))
```

---

## Execution Timeline

```
Week 1:  [Phase 1] Foundation
         └── Install + Test infrastructure

Week 2:  [Phase 2] Naukri
         [Phase 3] Internshala (parallel)
         └── Deploy job platform scrapers

Week 3:  [Phase 3 cont] Internshala (completion)
         [Phase 4 start] Government APIs
         └── Continue government integration

Week 4:  [Phase 4] Government APIs (continued)
         └── DPIIT, MCA21, GeM, MSME

Week 5:  [Phase 4 cont] Government APIs (completion)
         [Phase 5] LinkedIn + Others
         └── Finish govt, start additional platforms

Week 6:  [Phase 6] GBM Scoring
         └── Feature engineering + Model training

Week 7:  [Phase 7] LLM Scoring
         └── Qualitative analysis + Composite scorer

Week 8:  [Phase 8] Pipeline Integration
         └── Connect all components

Week 9:  [Phase 9] Performance
         └── Scale to 25K+ leads/day

Week 10: [Phase 10] Data Quality
         └── Ensure 90%+ accuracy

Week 11: [Phase 11] Testing
         └── Comprehensive test coverage

Week 12: [Phase 12] Deployment
         └── Production deployment
```

---

## Resource Allocation

```
Team Structure:
├── Backend Engineer (Full-time)
│   ├── Phase 1: Foundation
│   ├── Phase 4: Government APIs
│   ├── Phase 6: GBM Scoring
│   └── Phase 8: Pipeline Integration
│
├── Scraping Specialist (Full-time)
│   ├── Phase 2: Naukri
│   ├── Phase 3: Internshala
│   ├── Phase 5: LinkedIn + Others
│   └── Phase 9: Performance
│
├── ML Engineer (Part-time)
│   ├── Phase 6: GBM Scoring
│   ├── Phase 7: LLM Scoring
│   └── Phase 10: Data Quality
│
├── DevOps Engineer (Part-time)
│   ├── Phase 9: Performance
│   ├── Phase 11: Testing
│   └── Phase 12: Deployment
│
└── QA Engineer (Part-time)
    ├── Phase 10: Data Quality
    └── Phase 11: Testing
```

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation | Contingency |
|------|--------|-------------|------------|-------------|
| Naukri blocks scraper | HIGH | HIGH | Residential proxies, stealth | Fallback to HTML parsing |
| Government API changes | MEDIUM | MEDIUM | Version pinning | Fallback scraping |
| Model accuracy low | HIGH | LOW | Feature engineering | Tune hyperparameters |
| Memory issues at scale | MEDIUM | MEDIUM | Batch processing | Horizontal scaling |
| Data quality issues | HIGH | MEDIUM | Validation pipeline | Manual review process |
| Team member unavailable | MEDIUM | LOW | Cross-training | Contractor backup |

---

## Checkpoint Schedule

```
Daily: Standup (15 min)
  ├── What was completed yesterday
  ├── What is planned today
  └── Any blockers

Weekly: Sprint Review (1 hour)
  ├── Phase progress demo
  ├── Verification results
  ├── Issue resolution
  └── Next week planning

Bi-weekly: Architecture Review (2 hours)
  ├── Technical decisions
  ├── Architecture evolution
  └── Performance metrics

Monthly: Stakeholder Review (1 hour)
  ├── Progress report
  ├── Metrics dashboard
  ├── Risk assessment
  └── Budget review
```

---

## Success Metrics

| Metric | Target | Measurement Frequency |
|--------|--------|------------------------|
| Leads collected/day | 25,000+ | Daily |
| Data accuracy | >90% | Weekly |
| Scoring accuracy (ROC AUC) | >0.85 | Per model training |
| Pipeline latency | <5 min | Real-time |
| False positive rate | <10% | Weekly |
| Bot detection pass rate | >95% | Per deployment |
| API uptime | >99.9% | Real-time |
| Test coverage | >80% | Per build |

---

*Execution Orchestration Plan*
*Total Duration: 12 weeks*
*Parallel Groups: 6*
*Critical Path Length: 12 weeks*
