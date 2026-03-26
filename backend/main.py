"""
LeadIQ Backend — FastAPI Server
Phase 1: Core Infrastructure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config import settings
from backend.core.redis_client import redis_client
from backend.api import health, leads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()


app = FastAPI(
    title="LeadIQ API",
    description="AI Lead Intelligence Platform — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(leads.router, prefix="/api", tags=["leads"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
