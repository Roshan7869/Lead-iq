"""
scripts/debug_scoring.py — Debug the 12-dim scoring engine on a single post.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.engine.scorer import MultiDimensionalScorer

# Test a known strong signal post
text = """Ask HN: Looking for a cheaper alternative to Zendesk for our startup

We're a small team of 20 and Zendesk is getting too expensive as we scale. 
We need a customer support solution that doesn't break the bank. 
Budget is $500/month. Must have API access and good integrations."""

scorer = MultiDimensionalScorer()
score = scorer.score(text, sources=["hn"], recency_days=0)

print(f"Overall score: {score.overall}/100")
print(f"Confidence: {score.confidence}")
print(f"Sources: {score.sources}")
print("\nDimensions:")
for dim, val in sorted(score.dimensions.items(), key=lambda x: x[1], reverse=True):
    if val > 0:
        print(f"  {dim}: {val}/100")
print("\nReasoning:")
for r in score.reasoning:
    print(f"  - {r}")
