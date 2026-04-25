---
type: domain
name: Security
door: The-Gatehouse
issues: 22
severity: critical
---

# The Gatehouse — Security Domain

> "The first line of defense. Guards stand watch. The moat is deep. But some trapdoors are open."

## Guards at the Gate (Auth Endpoints)
- `/api/auth/login` — [[HIGH-018]] JWT query param leak
- `/api/auth/me` — [[HIGH-018]] Accepts token as query parameter
- `/api/auth/refresh` — [[HIGH-048]] No revocation mechanism

## Unlocked Doors (Missing Auth)
- `GET /api/leads` — [[CRIT-001]] 🔴 **CRITICAL** — Anyone can enumerate all leads
- `PATCH /api/lead/{id}` — [[CRIT-001]] 🔴 **CRITICAL** — Anyone can mutate leads
- `GET /api/stats/pipeline` — [[HIGH-020]] — Exposes pipeline stats
- `/api/mcp/*` — [[HIGH-019]] — MCP introspection unauthenticated

## Trapdoors (Injection / Leaks)
- `backend/api/routes/admin.py:183` — [[CRIT-014]] 🔴 **CRITICAL** — SQL injection via f-string
- `backend/shared/config.py:20` — [[HIGH-015]] — Hardcoded DB password
- `backend/shared/config.py:71` — [[HIGH-016]] — Hardcoded admin username
- `backend/services/auth.py:21-22` — [[HIGH-047]] — JWT secret cached at module load
- `backend/shared/logging_config.py:77` — Medium — Sentry DSN prefix logged

## Lockbox (Secrets Management)
- `.env.example` — Reference for all required secrets
- `backend/shared/config.py` — Pydantic BaseSettings (needs hardcoded defaults removed)

## Moat (CORS / Rate Limiting)
- `backend/main.py:86-92` — Medium — CORS `allow_credentials=True` with wildcards
- `src/middleware.ts` — Medium — Local `Map` rate limiter (resets on restart)

## Fix Order
1. [[CRIT-001]] Add auth to lead endpoints
2. [[CRIT-014]] Fix SQL injection f-string
3. [[HIGH-015]] Remove hardcoded DB password
4. [[HIGH-016]] Remove hardcoded admin username
5. [[HIGH-018]] Remove JWT query param support
6. [[HIGH-019]] Enforce MCP auth
7. [[HIGH-020]] Add auth to stats endpoint
8. [[HIGH-047]] Read JWT secret inside functions
9. [[HIGH-048]] Add refresh token blocklist

## Related
- [[The-Citadel]] ← Back to hub
- [[Phase-1-Stop-the-Bleeding]] ← Active phase
- [[Phase-2-Security-Hardening]] ← Next phase
