# 🧠 LeadIQ — AI Lead Intelligence Platform

> AI-powered demand signal detection, lead scoring, personalised outreach generation, and pipeline tracking.

---

## ✨ Features

| Feature | Status |
|---------|--------|
| AI demand signal detection | ✅ Simulated (Phase 3) |
| Deterministic lead scoring | ✅ Done (Phase 5) |
| Hot / Warm / Cold ranking | ✅ Done (Phase 6) |
| Personalised outreach generation | ✅ Done (Phase 7) |
| Kanban pipeline board | ✅ Done |
| AI Command Center terminal | ✅ Done |
| ROI Tracker | ✅ Done |
| REST API (Next.js routes) | ✅ Done |
| FastAPI backend + Redis streams | ✅ Scaffolded |
| PostgreSQL persistence | 🔄 Scaffolded (in-memory fallback) |
| Real LLM integration | 🔄 Planned (Phase 4) |
| Auth / multi-user | 🔄 Planned |

---

## 🏗️ Architecture

```
Frontend (Next.js 15 App Router)
  └── /src/app           — Next.js pages & API routes
  └── /src/views         — Page view components
  └── /src/components    — Shared UI components
  └── /src/hooks         — React context & hooks
  └── /src/data          — Static demo data

Backend (FastAPI)
  └── /backend/main.py   — FastAPI entrypoint
  └── /backend/core      — Redis client & config
  └── /backend/api       — REST endpoints
  └── /backend/workers   — Event-driven microworkers
  └── /backend/models    — SQLAlchemy ORM models
  └── /backend/schemas   — Pydantic schemas
  └── /backend/services  — CRM / persistence layer

Infrastructure
  └── /infra/docker-compose.yml   — Redis + PostgreSQL + Backend + Frontend
  └── /infra/Dockerfile.backend
  └── /infra/Dockerfile.frontend
```

### Event Bus (Redis Streams)

```
lead:collected → lead:analyzed → lead:scored → lead:ranked → lead:outreach → lead:crm_update
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- npm 10+

### 1. Clone & install

```bash
git clone https://github.com/Roshan7869/Lead-iq.git
cd Lead-iq
npm install --legacy-peer-deps
```

### 2. Configure environment

```bash
cp .env.example .env.local
# Edit .env.local with your values
```

### 3. Run development server

```bash
npm run dev
# Open http://localhost:3000
```

### 4. Build for production

```bash
npm run build
npm start
```

---

## 🐳 Docker (Full Stack)

```bash
cd infra
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Redis: localhost:6379
- PostgreSQL: localhost:5432

---

## 🔌 API Reference

All API routes are Next.js Route Handlers at `/src/app/api/`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/leads` | List all leads |
| `POST` | `/api/run-miner` | Trigger demand miner |
| `POST` | `/api/run-ai` | Trigger AI analyzer |
| `GET` | `/api/lead/[id]` | Get single lead |
| `PATCH` | `/api/lead/[id]` | Update lead stage/priority |

---

## 🌿 Environment Variables

See [`.env.example`](.env.example) for full documentation.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |
| `REDIS_URL` | Backend | `redis://localhost:6379` | Redis connection |
| `DATABASE_URL` | Backend | see example | PostgreSQL asyncpg URL |
| `ALLOWED_ORIGINS` | Backend | `["http://localhost:3000"]` | CORS origins |
| `DEBUG` | Backend | `False` | Debug mode |
| `OPENAI_API_KEY` | Optional | — | LLM integration |

---

## 📊 Performance Targets (Market-Ready Checkpoints)

| Metric | Target | Current |
|--------|--------|---------|
| First Load JS (all routes) | < 200 KB | 102–318 KB |
| Largest Contentful Paint | < 2.5 s | TBD |
| Time to Interactive | < 3.5 s | TBD |
| API response time | < 200 ms | TBD |
| Lighthouse Performance | > 90 | TBD |
| Lighthouse Accessibility | > 90 | TBD |
| Core Web Vitals (CLS) | < 0.1 | TBD |

---

## 🧪 Testing

```bash
# Unit tests
npm test

# Watch mode
npm run test:watch
```

---

## 📁 Project Structure

```
/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── layout.tsx        # Root layout with providers
│   │   ├── page.tsx          # / — Overview
│   │   ├── pipeline/         # /pipeline
│   │   ├── demand-miner/     # /demand-miner
│   │   ├── command-center/   # /command-center
│   │   ├── roi-tracker/      # /roi-tracker
│   │   └── api/              # Next.js API routes
│   ├── views/                # View-layer page components
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── enhanced/         # Feature-specific components
│   │   └── ...               # Layout, sidebar, modals
│   ├── hooks/                # use-leads, use-toast, use-mobile
│   ├── data/                 # Demo seed data
│   ├── types/                # TypeScript types
│   └── lib/                  # Utilities
├── backend/                  # FastAPI backend
├── infra/                    # Docker & deployment
├── public/                   # Static assets
├── .env.example              # Environment variable template
└── next.config.ts            # Next.js configuration
```

---

## 🔐 Security

- Security headers applied on all routes (X-Frame-Options, CSP, etc.)
- No secrets committed — see `.gitignore`
- CORS origins configured via `ALLOWED_ORIGINS` env var
- Backend uses pydantic-settings for type-safe config

---

## 🗺️ Roadmap

- [ ] Real LLM integration (OpenAI / Anthropic) for Phase 4 AI Analyzer
- [ ] PostgreSQL persistence (replace in-memory CRM store)
- [ ] Authentication (NextAuth.js or Clerk)
- [ ] Real-time updates via Redis Pub/Sub → SSE
- [ ] Email/LinkedIn outreach sending integration
- [ ] Multi-workspace / team support
- [ ] Webhook support for external CRM sync

