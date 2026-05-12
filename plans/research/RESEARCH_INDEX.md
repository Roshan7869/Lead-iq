# Research Papers Index
> Preserved research foundation for LeadIQ optimization
> Date: 2026-05-11
> Papers Analyzed: 15+

---

## CORE RESEARCH PAPERS

### Paper 1: SalesRLAgent
**File:** `papers/sales_rl_agent.md`  
**URL:** https://arxiv.org/abs/2503.23303  
**Authors:** Nandakishor Mukkunnoth  
**Date:** March 30, 2025  
**Venue:** arXiv:2503.23303 [cs.LG]

**Key Contributions:**
- Reinforcement Learning for real-time sales conversion prediction
- 96.7% accuracy in conversion prediction
- Outperforms LLM-only approaches by 34.7%
- 85ms inference (vs 3450ms for GPT-4)
- 43.2% increase in conversion rates with real-time guidance

**Implementation Strategy for LeadIQ:**
```python
class SalesRLScorer:
    """RL-based conversion prediction system"""
    def __init__(self):
        self.state_tracker = TurnByTurnStateTracker()
        self.meta_learner = MetaLearningModule()
        self.embedding_dim = 3072  # Azure OpenAI embeddings
    
    def predict_conversion(self, lead_features, conversation_history):
        """Predict conversion probability at each interaction"""
        state = self.state_tracker.encode(lead_features, conversation_history)
        probability = self.meta_learner.estimate(state)
        return {
            'probability': probability,
            'confidence': self.meta_learner.confidence(state),
            'recommended_action': self.meta_learner.action(state)
        }
```

---

### Paper 2: Gradient Boosting for B2B Lead Scoring
**File:** `papers/gradient_boosting_lead_scoring.md`  
**URL:** https://www.frontiersin.org/articles/10.3389/frai.2025.1554325  
**Authors:** Laura González-Flores, Jessica Rubiano-Moreno, Guillermo Sosa-Gómez  
**Date:** March 7, 2025  
**Venue:** Frontiers in Artificial Intelligence, Volume 8 - 2025

**Key Contributions:**
- Case study of B2B software company (Jan 2020 - Apr 2024)
- 15 classification algorithms evaluated
- Gradient Boosting Classifier achieves **98.39% accuracy**
- Top features: "source" and "lead status"
- ROC AUC superior to all other methods

**Feature Importance Rankings:**
1. Source (reddit/hn/twitter/job_platform/govt)
2. Lead status (new/contacted/qualified)
3. Company size
4. Industry match
5. Engagement depth
6. Days since first touch
7. Job posting velocity
8. Government registration status

**Implementation Strategy for LeadIQ:**
```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

class LeadScoringGBM:
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42
        )
        self.feature_names = [
            'source_encoded', 'lead_status_encoded',
            'company_size', 'industry_match',
            'engagement_depth', 'days_since_first_touch',
            'job_posting_velocity', 'govt_registration'
        ]
    
    def train(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred)
        print(f"ROC AUC: {auc:.4f}")
        
        return self.model
    
    def get_feature_importance(self):
        return dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
```

---

### Paper 3: VALOR (Value-Aware Revenue Uplift)
**File:** `papers/valor_uplift_modeling.md`  
**URL:** https://arxiv.org/abs/2604.02472  
**Authors:** Vamshi Guduguntla, Kavin Soni, Debanshu Das  
**Date:** April 2, 2026  
**Venue:** arXiv:2604.02472 [cs.LG]

**Key Contributions:**
- Treatment-Gated Sparse-Revenue Network
- Cost-Sensitive Focal-ZILN objective
- Robust ZILN-GBDT tree-based variant
- 20% improvement in rankability over SOTA
- **2.7x increase in incremental revenue** per account (4-month A/B test)

**Architecture:**
```
Input: Lead features + Treatment history
├── Treatment-Gated Network (bilinear interaction)
├── Sparse-Revenue Layer (prevents signal collapse)
├── Cost-Sensitive Focal Loss (handles zero-inflation)
└── Value-Weighted Ranking (scales by financial magnitude)

Output: Uplift score + revenue prediction
```

**Implementation Strategy for LeadIQ:**
```python
class VALORScorer:
    """Value-Aware Revenue Uplift Scoring"""
    def __init__(self):
        self.treatment_gater = TreatmentGatedNetwork()
        self.sparse_revenue = SparseRevenueLayer()
        self.focal_loss = CostSensitiveFocalZILN()
    
    def compute_uplift(self, lead, treatment_history):
        """Compute revenue uplift for a lead"""
        # Prevent treatment signal collapse
        gated_features = self.treatment_gater(lead, treatment_history)
        
        # Handle zero-inflated revenue distribution
        revenue_pred = self.sparse_revenue(gated_features)
        
        # Value-weighted ranking
        uplift = self.focal_loss.compute(revenue_pred, lead['historical_value'])
        
        return {
            'uplift_score': uplift,
            'revenue_prediction': revenue_pred,
            'treatment_recommendation': self.recommend_treatment(uplift)
        }
```

---

### Paper 4: CPOG Framework (LinkedIn)
**File:** `papers/cpog_causal_optimization.md`  
**URL:** https://arxiv.org/abs/2505.09847  
**Authors:** LinkedIn Research Team  
**Date:** May 21, 2025  
**Venue:** arXiv:2505.09847 [cs.LG]

**Key Contributions:**
- 3-layer architecture: Causal ML + Optimization + Generative AI
- Uplift models for sales action prioritization
- Constrained optimization for multi-objective balancing
- Explainable AI + Generative AI for recommendations
- Deployed at LinkedIn scale

**3-Layer Architecture:**
```
Layer 1: Prediction (Causal ML)
├── Uplift estimation using causal forests
├── Heterogeneous treatment effect estimation
└── Individual-level counterfactual prediction

Layer 2: Optimization (Constraint Optimization)
├── Multi-objective: revenue, conversion, cost
├── Contextual bandits for action selection
└── Budget and resource constraints

Layer 3: Serving (Generative AI + Feedback)
├── Natural language recommendations
├── Explainable action suggestions
└── Continuous feedback loop refinement
```

---

### Paper 5: Geo-DANN DeepScore
**File:** `papers/geo_dann_deepscore.md`  
**URL:** https://openreview.net/pdf?id=JbyaS5zhcB  
**Authors:** Anonymous (ICLR 2026 Under Review)  
**Date:** 2026  
**Venue:** ICLR 2026

**Key Contributions:**
- Geo-Invariant Lead Scoring with Domain-Adversarial Networks
- Transformer sequence modeling with geography alignment
- 4.3% relative gain in macro-AUPR
- 12.3% reduction in inter-region performance gaps
- 1.4M leads across 10 geographic markets

**Architecture:**
```python
class GeoDANNDeepScore:
    """Geography-aware lead scoring with domain adversarial training"""
    def __init__(self, num_geographies=10):
        self.encoder = TransformerEncoder()
        self.domain_classifier = DomainClassifier(num_geographies)
        self.grade_predictor = GradePredictor()
        self.dann_lambda = 0.1  # Domain adversarial weight
    
    def forward(self, lead_sequence, geography_id):
        # Extract features
        features = self.encoder(lead_sequence)
        
        # Domain adversarial component
        reversed_features = GradientReversalLayer(features)
        domain_pred = self.domain_classifier(reversed_features)
        
        # Prediction component
        grade = self.grade_predictor(features)
        
        # Loss: prediction - domain_adversarial
        loss = prediction_loss(grade) - self.dann_lambda * domain_loss(domain_pred, geography_id)
        
        return grade, loss
```

**For LeadIQ India:**
- Train separate encoders for each Indian state
- Use domain adversarial to ensure fairness across states
- Handle data imbalance (more leads from Karnataka/Maharashtra vs NE states)

---

### Paper 6: asLLR (LLM-based Leads Ranking)
**File:** `papers/asllr_llm_ranking.md`  
**URL:** https://arxiv.org/abs/2510.21713  
**Authors:** Yin Sun, Yiwen Liu, Junjie Song, et al.  
**Date:** September 10, 2025  
**Venue:** arXiv:2510.21713 [cs.IR]

**Key Contributions:**
- LLM-based lead ranking in auto sales
- Integrates CTR loss + QA loss in decoder-only architecture
- AUC 0.8127 (surpasses traditional CTR by 0.0231)
- **9.5% sales volume increase** in real-world A/B test
- 300K training samples, 40K testing samples

**Architecture:**
```python
class asLLRModel:
    """LLM-based Lead Ranking"""
    def __init__(self, base_model='llama-3-8b'):
        self.llm = load_decoder_only_model(base_model)
        self.ctr_head = CTRPredictionHead()
        self.qa_head = QAPredictionHead()
        self.text_summarizer = TextSummarizationModule()
    
    def forward(self, tabular_features, text_features):
        # Summarize long text features
        summarized_text = self.text_summarizer(text_features)
        
        # Combined input
        input_embedding = self.combine(tabular_features, summarized_text)
        
        # LLM processing
        hidden_states = self.llm(input_embedding)
        
        # Dual prediction heads
        ctr_score = self.ctr_head(hidden_states)
        qa_score = self.qa_head(hidden_states)
        
        # Combined loss
        total_loss = ctr_loss(ctr_score) + qa_loss(qa_score)
        
        return ctr_score, total_loss
```

---

### Paper 7: Scrapus AI Platform
**File:** `papers/scrapus_ai_lead_generation.md`  
**URL:** https://www.frontiersin.org/articles/10.3389/frai.2025.1606431  
**Authors:** Kaplan A, Seker SE, Yoruk R  
**Date:** 2025  
**Venue:** Frontiers in Artificial Intelligence, Volume 8

**Key Contributions:**
- AI-driven web prospecting platform
- Reinforcement learning for focused crawling (3x yield improvement)
- Transformer-based NLP for extraction (F1: 0.77 → 0.92)
- Knowledge-enhanced analysis for qualification
- **~90% precision and recall** in lead qualification

**Components:**
```
Scrapus Architecture:
├── RL-based Focused Crawler
│   ├── State: Page content + link structure
│   ├── Action: Which link to follow
│   └── Reward: Relevant company found
├── Transformer-based NLP Extractor
│   ├── Entity recognition (company, person, role)
│   ├── Relation extraction (works_at, founded)
│   └── Text summarization
├── Knowledge Graph Enrichment
│   ├── Link entities to known databases
│   ├── Infer missing attributes
│   └── Validate extracted data
└── LLM-based Summary Generator
    ├── Generate natural language lead summaries
    ├── Highlight key selling points
    └── Suggest outreach angles
```

---

## SUPPORTING RESEARCH

### Paper 8: AutoML for SME Lead Prediction
**URL:** https://qme.sggw.edu.pl/article/download/10769/9205/20168  
**Finding:** AutoML binary classification achieves >80% accuracy with <1% of annual income cost

### Paper 9: B2B Conversion Prediction Survey
**URL:** https://arxiv.org/pdf/2512.01171  
**Finding:** Comprehensive survey of 99 papers on CVR prediction in online advertising

### Paper 10: Predictive Lead Scoring Guide
**URL:** https://kumo.ai/resources/learn/guide/lead-scoring-complete-guide/  
**Finding:** Relational ML achieves 5-8x conversion lift over random

---

## RESEARCH SYNTHESIS FOR LEADIQ

### Optimal Architecture (Based on Research)

```python
class LeadIQOptimalScorer:
    """
    Hybrid scoring system combining all research insights:
    - Gradient Boosting for tabular features (Paper 2)
    - LLM for text analysis (Paper 6)
    - RL for sequential optimization (Paper 1)
    - Domain adversarial for geo-fairness (Paper 5)
    - Uplift modeling for revenue (Paper 3)
    """
    
    def __init__(self):
        # Layer 1: Gradient Boosting (tabular)
        self.gbm = GradientBoostingClassifier(n_estimators=200)
        
        # Layer 2: LLM (textual)
        self.llm_scorer = asLLRAdapter()
        
        # Layer 3: RL (sequential)
        self.rl_agent = SalesRLAdapter()
        
        # Layer 4: Uplift (revenue)
        self.valor = VALORAdapter()
        
        # Layer 5: Domain adaptation (geo-fairness)
        self.geo_dann = GeoDANNAdapter()
    
    def score_lead(self, lead_data):
        # Extract features
        tabular_features = self.extract_tabular(lead_data)
        text_features = self.extract_text(lead_data)
        sequential_features = self.extract_sequence(lead_data)
        
        # Layer predictions
        gbm_score = self.gbm.predict_proba(tabular_features)[:, 1]
        llm_score = self.llm_scorer.score(text_features)
        rl_score = self.rl_agent.predict(sequential_features)
        uplift_score = self.valor.compute_uplift(lead_data)
        geo_score = self.geo_dann.score(lead_data, lead_data['state'])
        
        # Weighted ensemble
        final_score = (
            0.30 * gbm_score +
            0.25 * llm_score +
            0.20 * rl_score +
            0.15 * uplift_score +
            0.10 * geo_score
        )
        
        return {
            'final_score': final_score,
            'component_scores': {
                'gbm': gbm_score,
                'llm': llm_score,
                'rl': rl_score,
                'uplift': uplift_score,
                'geo': geo_score
            },
            'confidence': self.compute_confidence(final_score),
            'recommended_action': self.recommend_action(final_score)
        }
```

---

*Research preserved for implementation reference*
*Total papers: 15+*  
*Research date: 2026-05-11*  
*Plan version: 1.0*
