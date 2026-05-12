"""
scripts/run_world_class_pipeline.py — Full end-to-end test of LeadIQ v3 world-class pipeline.
Runs ALL 4 collectors, scores, enriches, fuses, and outputs results.
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipeline_v3 import run_full_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("=== Running LeadIQ v3 World-Class Pipeline ===")
    result = await run_full_pipeline()

    leads = result["leads"]
    anomalies = result.get("anomalies", [])
    fusions = result.get("fusions", [])
    trends = result.get("trends", [])
    stats = result.get("stats", {})

    # Classify leads
    hot = [l for l in leads if l["score"].confidence == "HOT"]
    warm = [l for l in leads if l["score"].confidence == "WARM"]
    cool = [l for l in leads if l["score"].confidence == "COOL"]
    cold = [l for l in leads if l["score"].confidence == "COLD"]

    logger.info("\n🏆 RESULTS:")
    logger.info("HOT leads: %d", len(hot))
    logger.info("WARM leads: %d", len(warm))
    logger.info("COOL leads: %d", len(cool))
    logger.info("COLD leads: %d", len(cold))
    logger.info("Anomalies: %d", len(anomalies))
    logger.info("Fusions: %d", len(fusions))
    logger.info("Trends: %d", len(trends))

    # Show top HOT/WARM with enrichment
    logger.info("\n--- TOP HOT LEADS ---")
    for l in hot[:3]:
        p = l["post"]
        s = l["score"]
        persona = l.get("persona")
        logger.info("🔥 [%s] %d/100 | %s | Sources: %s",
            s.confidence, s.overall, p.title[:60],
            ", ".join(s.sources))
        if persona:
            logger.info("   👤 %s @ %s | Email: %s | Tech: %s",
                persona.role, persona.company or "Unknown",
                persona.email_pattern or "N/A",
                ", ".join(persona.tech_stack[:5]) if persona.tech_stack else "N/A")

    logger.info("\n--- TOP WARM LEADS ---")
    for l in warm[:3]:
        p = l["post"]
        s = l["score"]
        logger.info("🌡 [%s] %d/100 | %s", s.confidence, s.overall, p.title[:60])

    # Show anomalies
    if anomalies:
        logger.info("\n🚨 ANOMALIES DETECTED:")
        for a in anomalies[:3]:
            logger.info("   %s (z=%.2f)", a.get("signal_type"), a.get("z_score"))

    # Show fusions
    if fusions:
        logger.info("\n🔗 SIGNAL FUSIONS:")
        for f in fusions[:3]:
            logger.info("   %s across %s (score: %d)",
                f["entities"][0] if f["entities"] else "Unknown",
                ", ".join(f["sources"]),
                f["fusion_score"])

    logger.info("\n✅ Pipeline complete. World-class intelligence delivered. Zero paid APIs used.")


if __name__ == "__main__":
    asyncio.run(main())
