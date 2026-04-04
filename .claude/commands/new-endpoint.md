---
description: Scaffold a complete FastAPI endpoint with model, service, route, test
---

Create endpoint: $ARGUMENTS

Read first (NO CODE):
  backend/models/ (check if model exists)
  backend/schemas/ (check if schema exists)
  backend/routes/ (find correct route file)

Build in this exact order:

1. SQLAlchemy model in backend/models/ (if missing)
   - UUID id, created_at, updated_at always present
   - Async-compatible
   - Show Alembic command (do NOT run it)

2. Pydantic v2 schemas in backend/schemas/:
   - [Model]Create (input)
   - [Model]Read (output, inherits from Base + id + timestamps)
   - [Model]Update (partial, all fields Optional)

3. Service function in backend/services/[model]_service.py:
   - Async function signature with type hints
   - structlog for all logging
   - No business logic in routes

4. Route in backend/routes/ (correct file for this endpoint):
   - Dependency injection for db session and current user
   - Input validated via Pydantic schema
   - LeadEvent log if endpoint touches a Lead record

5. pytest test in tests/routes/test_[endpoint].py:
   - Mock DB session
   - Test: happy path, 404, 422 validation error
   - Run tests: pytest tests/routes/test_[endpoint].py -v

Show each file completely before writing. Ask approval before writing.