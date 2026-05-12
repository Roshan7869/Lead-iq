"""Mark Richards fitness function: Next.js MUST never contain business logic."""
import os
import pytest

BUSINESS_LOGIC_KEYWORDS = [
    "score", "enrich", "icp_score", "gemini", "analyze",
    "intent", "rank", "filter", "transform", "opportunity",
]

NEXTJS_API_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "src", "app", "api"
)


def _get_all_route_files():
    route_files = []
    if not os.path.exists(NEXTJS_API_DIR):
        return route_files
    for root, _, files in os.walk(NEXTJS_API_DIR):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                route_files.append(os.path.join(root, f))
    return route_files


@pytest.mark.parametrize("filepath", _get_all_route_files())
def test_no_business_logic_in_nextjs_routes(filepath):
    with open(filepath) as f:
        content = f.read().lower()
    violations = [kw for kw in BUSINESS_LOGIC_KEYWORDS if kw in content]
    assert not violations, (
        f"Business logic found in Next.js route {filepath}: {violations}. "
        "FastAPI must own all business logic."
    )
