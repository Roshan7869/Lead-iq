"""
Mark Richards Architectural Fitness Functions
"""
import ast, os, re, pytest
from pathlib import Path

def py_files(directory: str) -> list[Path]:
    return list(Path(directory).rglob("*.py"))

def read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_no_sync_db_calls():
    """ALL database calls must be async"""
    sync_orm_patterns = [r"session\.query\("]
    violations = []
    for f in py_files("backend/"):
        content = read(f)
        if re.search(r"session\.query\(", content):
            violations.append(f"{f}: session.query() — use await db.execute(select(...))")
    assert not violations, f"Sync DB calls found:\n" + "\n".join(violations)


def test_no_print_statements():
    """Use structlog only — print() breaks structured logging"""
    violations = []
    for f in py_files("backend/") + py_files("workers/"):
        if "test_" in str(f):
            continue
        try:
            tree = ast.parse(read(f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    violations.append(f"{f}:line {node.lineno}")
    assert not violations, f"print() found (use structlog):\n" + "\n".join(violations)


def test_all_collector_routes_have_rate_limits():
    """Every collector POST endpoint must have @limiter.limit"""
    collectors_file = Path("backend/api/routes/leads.py")
    if collectors_file.exists():
        content = read(collectors_file)
        post_routes = len(re.findall(r'@router\.(post|get|put|delete)', content))
        rate_limits = len(re.findall(r'@limiter\.limit', content))
        assert rate_limits >= post_routes, (
            f"Rate limit mismatch: {post_routes} routes but only {rate_limits} limits"
        )


def test_no_hardcoded_secrets():
    """Zero secrets in any Python file"""
    secret_patterns = [
        (r'sk-ant-api', "Anthropic key"),
        (r'AIzaSy[0-9A-Za-z_-]{33}', "Google API key"),
        (r'ghp_[0-9A-Za-z]{36}', "GitHub PAT"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    ]
    violations = []
    all_files = py_files("backend/") + py_files("workers/")
    for f in all_files:
        try:
            content = read(f)
        except Exception:
            continue
        for pattern, desc in secret_patterns:
            if re.search(pattern, content):
                violations.append(f"{f}: possible {desc}")
    assert not violations, "Secrets in code:\n" + "\n".join(violations)


def test_gemini_calls_guarded_by_cost_check():
    """Every Gemini API call must be preceded by check_budget()"""
    gemini_file = Path("backend/llm/gemini_service.py")
    if gemini_file.exists():
        content = read(gemini_file)
        gemini_calls = len(re.findall(r'generate_content|embed_content|get_embedding', content))
        budget_checks = len(re.findall(r'check_budget', content))
        assert budget_checks >= gemini_calls, (
            f"Unguarded Gemini calls: {gemini_calls} API calls "
            f"but only {budget_checks} budget checks"
        )


def test_lead_model_required_fields_unchanged():
    """Core Lead schema contract"""
    try:
        from backend.models.lead import Lead
    except ImportError:
        pytest.skip("Lead model not found")
    # Check required fields exist
    required = ["company_name", "source", "confidence"]
    for field in required:
        assert hasattr(Lead, field), f"Required field '{field}' missing"


def test_supavisor_port_configured():
    """Must use port 6543, not 5432"""
    db_files = ["backend/shared/db.py", "backend/shared/config.py"]
    for path in db_files:
        if Path(path).exists():
            content = read(path)
            assert ":6543" in content or ":5432" not in content, (
                f"{path} should use port 6543 (Supavisor)"
            )
            return
    pytest.skip("DB config file not found")
