# Phases 6-7: ML Scoring Engine
> Duration: Week 6-7
> Priority: CRITICAL
> Dependencies: Phase 1 (Foundation)
> Research Basis: Gradient Boosting (Frontiers 2025), SalesRLAgent (arXiv 2503.23303), asLLR (arXiv 2510.21713), VALOR (arXiv 2604.02472)

---

## Phase 6: Gradient Boosting Scoring Model

### Objective
Replace heuristic scoring with research-backed Gradient Boosting Classifier achieving 98.39% accuracy.

### Implementation

```python
# backend/ml/scoring_model.py
"""
Gradient Boosting Lead Scoring Model
Based on: Frontiers 2025 - "The relevance of lead prioritization"
Achieves 98.39% accuracy, outperforms 15 other algorithms
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, precision_recall_curve, classification_report
import joblib
import structlog

logger = structlog.get_logger()

class GradientBoostingScorer:
    """GBM-based lead scoring engine"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_importance = {}
        self.model_path = model_path or "models/gbm_scorer.pkl"
        
        # Feature names (MUST match training order)
        self.feature_names = [
            # Fit signals (30%)
            'source_encoded',
            'lead_status_encoded',
            'company_size_encoded',
            'industry_match',
            'location_tier',
            'govt_registered',
            'dpiit_recognized',
            
            # Behavioral signals (35%)
            'page_views',
            'email_opens',
            'email_clicks',
            'job_engagement_score',
            'content_downloads',
            'days_since_first_touch',
            
            # Intent signals (35%)
            'hiring_velocity',
            'funding_recency',
            'govt_tender_count',
            'job_posting_count',
            'salary_range_encoded',
            'experience_level',
            'skills_match_score',
            
            # Indian-specific (bonus)
            'gst_verified',
            'udyam_verified',
            'cin_verified',
            'gem_vendor',
            'iit_founder',
        ]
        
    def train(self, leads: List[Lead], conversions: List[bool]) -> Dict:
        """Train GBM on historical lead + conversion data"""
        
        logger.info("gbm_training_start", 
                   n_samples=len(leads),
                   n_conversions=sum(conversions))
        
        # Extract features
        X = pd.DataFrame([
            self._extract_features(lead) 
            for lead in leads
        ])
        
        y = np.array(conversions)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Initialize GBM with optimal hyperparameters
        # Based on Frontiers 2025 research
        self.model = GradientBoostingClassifier(
            n_estimators=200,        # Optimal from research
            max_depth=6,             # Prevents overfitting
            learning_rate=0.1,       # Balanced convergence
            subsample=0.8,           # Reduces variance
            min_samples_split=20,    # Minimum split size
            min_samples_leaf=10,     # Minimum leaf size
            max_features='sqrt',     # Feature subsampling
            random_state=42,
            verbose=1
        )
        
        # Train
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_pred_proba)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='roc_auc')
        
        # Feature importance
        self.feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
        
        # Save model
        joblib.dump(self.model, self.model_path)
        
        metrics = {
            'roc_auc': auc,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': self.feature_importance,
            'n_features': len(self.feature_names),
            'n_samples': len(leads),
        }
        
        logger.info("gbm_training_complete", **metrics)
        
        return metrics
        
    def predict(self, lead: Lead) -> float:
        """Predict conversion probability for a lead"""
        
        if self.model is None:
            self._load_model()
            
        features = self._extract_features(lead)
        X = pd.DataFrame([features])
        X = X.fillna(0)
        
        # Predict probability
        probability = self.model.predict_proba(X)[0, 1]
        
        return probability
        
    def _extract_features(self, lead: Lead) -> Dict:
        """Extract structured features from lead"""
        
        return {
            # Fit signals
            'source_encoded': self._encode_source(lead.source),
            'lead_status_encoded': self._encode_status(lead.stage),
            'company_size_encoded': self._encode_company_size(lead.company_size),
            'industry_match': self._compute_industry_match(lead.industry),
            'location_tier': self._encode_location_tier(lead.location),
            'govt_registered': int(bool(lead.gst_number or lead.udyam_number or lead.cin_number)),
            'dpiit_recognized': int(lead.source == 'dpiit'),
            
            # Behavioral signals
            'page_views': lead.engagement_metrics.get('page_views', 0),
            'email_opens': lead.engagement_metrics.get('email_opens', 0),
            'email_clicks': lead.engagement_metrics.get('email_clicks', 0),
            'job_engagement_score': self._compute_job_engagement(lead),
            'content_downloads': lead.engagement_metrics.get('downloads', 0),
            'days_since_first_touch': self._days_since(lead.collected_at),
            
            # Intent signals
            'hiring_velocity': lead.raw_meta.get('job_count', 0),
            'funding_recency': self._encode_funding_recency(lead.raw_meta.get('funding_date')),
            'govt_tender_count': lead.raw_meta.get('tender_count', 0),
            'job_posting_count': lead.raw_meta.get('job_count', 0),
            'salary_range_encoded': self._encode_salary(lead.salary_range_min, lead.salary_range_max),
            'experience_level': self._encode_experience(lead.experience_required),
            'skills_match_score': self._compute_skills_match(lead.skills),
            
            # Indian-specific
            'gst_verified': int(bool(lead.gst_number)),
            'udyam_verified': int(bool(lead.udyam_number)),
            'cin_verified': int(bool(lead.cin_number)),
            'gem_vendor': int(lead.source == 'gem'),
            'iit_founder': int(self._check_iit_founder(lead.raw_meta.get('founder_name', ''))),
        }
        
    def _encode_source(self, source: str) -> int:
        """Encode source to numeric"""
        source_map = {
            'naukri': 10, 'internshala': 9, 'linkedin': 8,
            'dpiit': 7, 'mca21': 6, 'gem': 5, 'msme': 5,
            'reddit': 3, 'hn': 3, 'github': 2, 'twitter': 1,
        }
        return source_map.get(source, 0)
        
    def _encode_status(self, status: str) -> int:
        """Encode lead status"""
        status_map = {
            'closed_won': 10, 'qualified': 8, 'contacted': 5,
            'new': 3, 'closed_lost': 0,
        }
        return status_map.get(status, 0)
        
    def _encode_company_size(self, size: str) -> int:
        """Encode company size"""
        size_map = {
            'enterprise': 10, 'mid_market': 7,
            'smb': 5, 'startup': 8, 'individual': 2,
        }
        return size_map.get(size, 0)
        
    def _compute_industry_match(self, industry: str) -> float:
        """Compute industry match score (0-1)"""
        target_industries = ['saas', 'fintech', 'healthtech', 'edtech', 'ai_ml']
        return 1.0 if industry and industry.lower() in target_industries else 0.5
        
    def _encode_location_tier(self, location: str) -> int:
        """Encode location tier"""
        tier1 = ['bangalore', 'hyderabad', 'mumbai', 'delhi', 'pune', 'chennai']
        tier2 = ['kolkata', 'ahmedabad', 'jaipur', 'indore', 'nagpur']
        
        loc = location.lower() if location else ''
        if any(t in loc for t in tier1):
            return 3
        elif any(t in loc for t in tier2):
            return 2
        return 1
        
    def _compute_job_engagement(self, lead: Lead) -> float:
        """Compute job engagement score"""
        if lead.source in ['naukri', 'internshala', 'linkedin']:
            return 1.0
        return 0.0
        
    def _days_since(self, date: datetime) -> int:
        """Compute days since date"""
        if not date:
            return 365
        return (datetime.now() - date).days
        
    def _encode_funding_recency(self, funding_date: str) -> float:
        """Encode funding recency"""
        if not funding_date:
            return 0.0
        try:
            date = datetime.strptime(funding_date, '%Y-%m-%d')
            months_ago = (datetime.now() - date).days / 30
            if months_ago <= 6:
                return 1.0
            elif months_ago <= 12:
                return 0.7
            elif months_ago <= 24:
                return 0.4
            return 0.1
        except:
            return 0.0
            
    def _encode_salary(self, min_sal: int, max_sal: int) -> int:
        """Encode salary range"""
        avg = ((min_sal or 0) + (max_sal or 0)) / 2
        if avg >= 2000000:  # 20+ LPA
            return 5
        elif avg >= 1000000:  # 10-20 LPA
            return 4
        elif avg >= 500000:   # 5-10 LPA
            return 3
        elif avg >= 300000:   # 3-5 LPA
            return 2
        return 1
        
    def _encode_experience(self, exp: str) -> int:
        """Encode experience level"""
        if not exp:
            return 0
        try:
            import re
            nums = re.findall(r'(\d+)', exp)
            if nums:
                years = int(nums[0])
                if years >= 10:
                    return 5
                elif years >= 5:
                    return 4
                elif years >= 3:
                    return 3
                elif years >= 1:
                    return 2
                return 1
        except:
            pass
        return 0
        
    def _compute_skills_match(self, skills: List[str]) -> float:
        """Compute skills match score"""
        target_skills = ['python', 'react', 'aws', 'kubernetes', 'ai', 'ml']
        if not skills:
            return 0.0
        matches = sum(1 for s in skills if s.lower() in target_skills)
        return matches / len(target_skills)
        
    def _check_iit_founder(self, name: str) -> bool:
        """Check if founder is from IIT"""
        if not name:
            return False
        return 'iit' in name.lower()
        
    def _load_model(self):
        """Load trained model from disk"""
        try:
            self.model = joblib.load(self.model_path)
            logger.info("gbm_model_loaded", path=self.model_path)
        except FileNotFoundError:
            logger.error("gbm_model_not_found", path=self.model_path)
            raise
```

### 6.2 Feature Engineering Pipeline

```python
# backend/ml/feature_engineering.py
"""
Feature Engineering Pipeline
Transforms raw lead data into ML-ready features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class FeatureEngineer:
    """Engineer features from lead data"""
    
    def __init__(self):
        self.scaler = None
        self.encoders = {}
        
    def transform(self, lead: Lead) -> pd.Series:
        """Transform single lead to feature vector"""
        
        features = {}
        
        # Temporal features
        features['days_since_collected'] = self._days_since(lead.collected_at)
        features['days_since_enriched'] = self._days_since(lead.enriched_at)
        features['days_since_scored'] = self._days_since(lead.scored_at)
        
        # Source quality
        features['source_tier'] = self._source_tier(lead.source)
        features['source_age_days'] = self._source_age(lead.source)
        
        # Engagement velocity
        features['engagement_velocity'] = self._engagement_velocity(lead)
        features['engagement_acceleration'] = self._engagement_acceleration(lead)
        
        # Company signals
        features['company_age_years'] = self._company_age(lead)
        features['employee_growth_rate'] = lead.raw_meta.get('employee_growth_rate', 0)
        features['hiring_momentum'] = self._hiring_momentum(lead)
        
        # Market signals
        features['market_momentum'] = self._market_momentum(lead.industry)
        features['competitive_intensity'] = self._competitive_intensity(lead.industry, lead.location)
        
        # Intent recency
        features['intent_recency'] = self._intent_recency(lead)
        features['intent_frequency'] = self._intent_frequency(lead)
        
        return pd.Series(features)
        
    def _engagement_velocity(self, lead: Lead) -> float:
        """Compute engagement velocity (events per week)"""
        events = lead.engagement_metrics.get('total_events', 0)
        days = self._days_since(lead.collected_at)
        weeks = max(days / 7, 1)
        return events / weeks
        
    def _engagement_acceleration(self, lead: Lead) -> float:
        """Compute engagement acceleration"""
        recent_events = lead.engagement_metrics.get('events_last_7_days', 0)
        previous_events = lead.engagement_metrics.get('events_previous_7_days', 0)
        
        if previous_events == 0:
            return 1.0 if recent_events > 0 else 0.0
            
        return (recent_events - previous_events) / previous_events
        
    def _hiring_momentum(self, lead: Lead) -> float:
        """Compute hiring momentum score"""
        job_count = lead.raw_meta.get('job_count', 0)
        
        if job_count == 0:
            return 0.0
        elif job_count <= 3:
            return 0.3
        elif job_count <= 10:
            return 0.6
        elif job_count <= 25:
            return 0.8
        return 1.0
        
    def _source_tier(self, source: str) -> int:
        """Compute source tier quality"""
        tiers = {
            'naukri': 3, 'internshala': 3, 'linkedin': 3,
            'dpiit': 3, 'mca21': 3, 'gem': 3,
            'reddit': 2, 'hn': 2, 'github': 2,
            'twitter': 1,
        }
        return tiers.get(source, 0)
        
    def _market_momentum(self, industry: str) -> float:
        """Compute market momentum for industry"""
        # Based on industry growth rates
        momentum = {
            'ai_ml': 1.0, 'fintech': 0.9, 'healthtech': 0.9,
            'saas': 0.8, 'ecommerce': 0.7, 'edtech': 0.7,
        }
        return momentum.get(industry, 0.5)
        
    def _competitive_intensity(self, industry: str, location: str) -> float:
        """Compute competitive intensity in location"""
        # High competition = more hiring = better signal
        competitive_locations = ['bangalore', 'hyderabad', 'pune', 'chennai']
        loc = location.lower() if location else ''
        base_intensity = 0.7 if any(l in loc for l in competitive_locations) else 0.4
        
        competitive_industries = ['ai_ml', 'fintech', 'saas']
        ind = industry.lower() if industry else ''
        if any(i in ind for i in competitive_industries):
            base_intensity += 0.2
            
        return min(1.0, base_intensity)
```

---

## Phase 7: Hybrid LLM Scoring

### Objective
Add LLM qualitative analysis layer to augment GBM with text understanding.

### Implementation

```python
# backend/ml/qualitative_scorer.py
"""
LLM-based Qualitative Scorer
Based on: asLLR (arXiv 2510.21713) - AUC 0.8127, 9.5% sales increase
"""
import json
from typing import Dict, List
import structlog

from backend.llm.gemini_service import GeminiService

logger = structlog.get_logger()

class LLMQualitativeScorer:
    """LLM-based qualitative lead analysis"""
    
    def __init__(self):
        self.llm = GeminiService()
        
    async def analyze(self, lead: Lead) -> Dict:
        """Perform qualitative analysis of lead"""
        
        # Build prompt with lead context
        prompt = self._build_prompt(lead)
        
        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistency
            max_tokens=500
        )
        
        # Parse response
        result = self._parse_response(response)
        
        logger.info("llm_qualitative_analysis",
                   lead_id=lead.id,
                   score=result['qualitative_score'])
        
        return result
        
    def _build_prompt(self, lead: Lead) -> str:
        """Build analysis prompt for lead"""
        
        return f"""Analyze this B2B lead and score its quality for outreach.

Company: {lead.company_name or 'Unknown'}
Industry: {lead.industry or 'Unknown'}
Source: {lead.source}
Location: {lead.location or 'Unknown'}
Job Title: {lead.job_title or 'N/A'}
Skills: {', '.join(lead.skills or [])}
Experience Required: {lead.experience_required or 'N/A'}
Salary Range: {lead.salary_range_min or 'N/A'} - {lead.salary_range_max or 'N/A'}
Company Size: {lead.company_size or 'Unknown'}

Description: {lead.body or 'N/A'}

Recent Signals:
- Government Registered: {'Yes' if lead.gst_number or lead.udyam_number else 'No'}
- DPIIT Recognized: {'Yes' if lead.source == 'dpiit' else 'No'}
- Active Hiring: {'Yes' if lead.raw_meta.get('job_count', 0) > 0 else 'No'}
- Funding Stage: {lead.raw_meta.get('funding_stage', 'Unknown')}

Return JSON with:
{{
    "qualitative_score": integer 0-100,
    "buying_signals": [list of observed buying signals],
    "objection_risks": [list of potential objections],
    "company_maturity": "early_growth" | "scaling" | "enterprise",
    "budget_indicators": "high" | "medium" | "low",
    "recommended_approach": "one-sentence outreach strategy",
    "priority_reasoning": "why this lead is high/medium/low priority"
}}
"""
        
    def _parse_response(self, response: str) -> Dict:
        """Parse LLM response to structured output"""
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                return {
                    'qualitative_score': result.get('qualitative_score', 50),
                    'buying_signals': result.get('buying_signals', []),
                    'objection_risks': result.get('objection_risks', []),
                    'company_maturity': result.get('company_maturity', 'unknown'),
                    'budget_indicators': result.get('budget_indicators', 'medium'),
                    'recommended_approach': result.get('recommended_approach', ''),
                    'priority_reasoning': result.get('priority_reasoning', ''),
                }
        except Exception as e:
            logger.error("llm_response_parse_failed", error=str(e))
            
        return {
            'qualitative_score': 50,
            'buying_signals': [],
            'objection_risks': [],
            'company_maturity': 'unknown',
            'budget_indicators': 'medium',
            'recommended_approach': '',
            'priority_reasoning': '',
        }
```

### 7.2 Composite Scorer

```python
# backend/ml/composite_scorer.py
"""
Composite Scorer: GBM + LLM + RL + Uplift + Geo
Based on: VALOR (arXiv 2604.02472), Geo-DANN (ICLR 2026)
"""
from typing import Dict
import structlog

from backend.ml.scoring_model import GradientBoostingScorer
from backend.ml.qualitative_scorer import LLMQualitativeScorer
from backend.ml.rl_scorer import RLSequentialScorer
from backend.ml.uplift_scorer import UpliftRevenueScorer
from backend.ml.geo_scorer import GeoFairnessScorer

logger = structlog.get_logger()

class CompositeScorer:
    """Ensemble scorer combining all research-backed methods"""
    
    def __init__(self):
        self.gbm = GradientBoostingScorer()
        self.llm = LLMQualitativeScorer()
        self.rl = RLSequentialScorer()
        self.uplift = UpliftRevenueScorer()
        self.geo = GeoFairnessScorer()
        
        # Dynamic weights (can be tuned via Optuna)
        self.weights = {
            'gbm': 0.30,
            'llm': 0.25,
            'rl': 0.20,
            'uplift': 0.15,
            'geo': 0.10,
        }
        
    async def score(self, lead: Lead) -> ScoringResult:
        """Compute composite score using all models"""
        
        # Run all scorers in parallel
        import asyncio
        
        results = await asyncio.gather(
            self._score_gbm(lead),
            self._score_llm(lead),
            self._score_rl(lead),
            self._score_uplift(lead),
            self._score_geo(lead),
            return_exceptions=True
        )
        
        # Extract scores
        gbm_score = results[0] if not isinstance(results[0], Exception) else 0.5
        llm_score = results[1] if not isinstance(results[1], Exception) else 50
        rl_score = results[2] if not isinstance(results[2], Exception) else 0.5
        uplift_score = results[3] if not isinstance(results[3], Exception) else 0.5
        geo_score = results[4] if not isinstance(results[4], Exception) else 0.5
        
        # Normalize scores to 0-100
        gbm_norm = gbm_score * 100
        llm_norm = llm_score  # Already 0-100
        rl_norm = rl_score * 100
        uplift_norm = uplift_score * 100
        geo_norm = geo_score * 100
        
        # Weighted composite
        final_score = (
            self.weights['gbm'] * gbm_norm +
            self.weights['llm'] * llm_norm +
            self.weights['rl'] * rl_norm +
            self.weights['uplift'] * uplift_norm +
            self.weights['geo'] * geo_norm
        )
        
        # Classification band
        band = self._classify_band(final_score)
        
        return ScoringResult(
            final_score=final_score,
            band=band,
            component_scores={
                'gbm': gbm_norm,
                'llm': llm_norm,
                'rl': rl_norm,
                'uplift': uplift_norm,
                'geo': geo_norm,
            },
            confidence=self._compute_confidence(results),
            recommended_action=self._recommend_action(band),
            explanation=self._generate_explanation(lead, final_score)
        )
        
    async def _score_gbm(self, lead: Lead) -> float:
        return self.gbm.predict(lead)
        
    async def _score_llm(self, lead: Lead) -> float:
        result = await self.llm.analyze(lead)
        return result['qualitative_score'] / 100.0
        
    async def _score_rl(self, lead: Lead) -> float:
        return self.rl.predict(lead)
        
    async def _score_uplift(self, lead: Lead) -> float:
        return self.uplift.compute(lead)
        
    async def _score_geo(self, lead: Lead) -> float:
        return self.geo.adjust(lead, lead.location)
        
    def _classify_band(self, score: float) -> str:
        if score >= 75:
            return 'hot'
        elif score >= 50:
            return 'warm'
        elif score >= 25:
            return 'cool'
        return 'cold'
        
    def _compute_confidence(self, results: list) -> float:
        """Compute confidence based on model agreement"""
        # High agreement = high confidence
        # Use variance across models
        scores = [r for r in results if not isinstance(r, Exception)]
        if len(scores) < 2:
            return 0.5
        import numpy as np
        variance = np.var(scores)
        confidence = 1.0 - min(variance * 4, 1.0)  # Scale variance
        return confidence
        
    def _recommend_action(self, band: str) -> str:
        actions = {
            'hot': 'immediate_outreach',
            'warm': 'nurture_sequence',
            'cool': 'long_term_nurture',
            'cold': 'drip_campaign'
        }
        return actions.get(band, 'review')
        
    def _generate_explanation(self, lead: Lead, score: float) -> str:
        return f"Score {score:.1f} based on {lead.source} signals, " \
               f"{lead.raw_meta.get('job_count', 0)} job postings, " \
               f"government registration: {bool(lead.gst_number)}"
```

---

## Verification Checkpoints

### Checkpoint 6.1: GBM Training
- [ ] Train on 1000+ historical leads
- [ ] ROC AUC > 0.85
- [ ] Cross-validation mean > 0.80
- [ ] Feature importance extracted
- [ ] Model saved to disk

### Checkpoint 6.2: Feature Engineering
- [ ] All 25 features extracted correctly
- [ ] No missing values in test data
- [ ] Feature scaling applied
- [ ] Categorical encoding working

### Checkpoint 7.1: LLM Analysis
- [ ] Qualitative score 0-100 range
- [ ] Buying signals extracted
- [ ] Objection risks identified
- [ ] Response parsing robust

### Checkpoint 7.2: Composite Scoring
- [ ] All 5 models run successfully
- [ ] Weighted score 0-100 range
- [ ] Band classification correct
- [ ] Confidence score computed

---

*Phases 6-7 - ML Scoring Engine*
*Duration: Week 6-7*
*Target accuracy: >85%*
*Expected improvement: 3-5x over heuristic*
