"""
shared/models.py — SQLAlchemy ORM table definitions.
Keep this file open when writing any repository, worker, or route — Copilot
infers exact column names and types from here.

Tables:
  posts        — raw scraped content from collectors
  leads        — scored/ranked demand signals
  feedback     — human feedback on lead quality (reinforcement loop)
  quota_usage  — Gemini API token tracking per day
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.shared.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Post(Base):
    """Raw content scraped from a collector (Reddit, HN, Twitter, RSS, GitHub)."""

    __tablename__ = "posts"

    id: str = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: str = Column(String(32), nullable=False, index=True)          # reddit | hn | twitter | rss | github
    external_id: str = Column(String(256), nullable=False)                # platform-native ID
    url: str = Column(Text, nullable=False)
    title: str = Column(Text, nullable=True)
    body: str = Column(Text, nullable=True)
    author: str = Column(String(256), nullable=True)
    score: int = Column(Integer, default=0)                               # upvotes / reposts
    content_hash: str = Column(String(64), nullable=False, index=True)    # SHA-256 hex
    raw_meta: dict = Column(JSONB, nullable=True)                          # source-specific extras
    collected_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)

    lead = relationship("Lead", back_populates="post", uselist=False)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_post_source_ext"),
    )


class Lead(Base):
    """Enriched, scored demand signal ready for outreach."""

    __tablename__ = "leads"

    id: str = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: str = Column(UUID(as_uuid=False), ForeignKey("posts.id"), nullable=True, index=True)

    # ── Classification ───────────────────────────────────────────────────────
    is_opportunity: bool = Column(Boolean, default=False, nullable=False)
    confidence: float = Column(Float, default=0.0, nullable=False)        # 0.0–1.0
    intent: str = Column(String(64), nullable=True)                       # buy | evaluate | pain | compare
    urgency: str = Column(String(16), nullable=True)                      # high | medium | low

    # ── Score ────────────────────────────────────────────────────────────────
    opportunity_score: float = Column(Float, default=0.0, nullable=False)  # 0–100
    icp_fit_score: float = Column(Float, default=0.0, nullable=False)      # 0–100
    final_score: float = Column(Float, default=0.0, nullable=False)        # weighted composite
    score_band: str = Column(String(16), default="cold", nullable=False)   # hot | warm | cool | cold

    # ── Contact / Company ────────────────────────────────────────────────────
    company_name: str = Column(String(256), nullable=True)
    company_size: str = Column(String(32), nullable=True)                   # startup | smb | enterprise
    industry: str = Column(String(128), nullable=True)
    contact_name: str = Column(String(256), nullable=True)
    contact_title: str = Column(String(256), nullable=True)

    # ── CRM pipeline ─────────────────────────────────────────────────────────
    stage: str = Column(String(32), default="new", nullable=False)         # new | contacted | qualified | closed
    priority: str = Column(String(16), default="medium", nullable=False)   # high | medium | low
    notes: str = Column(Text, nullable=True)

    # ── Outreach ──────────────────────────────────────────────────────────────
    outreach_draft: str = Column(Text, nullable=True)
    outreach_sent_at: datetime = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    analyzed_at: datetime = Column(DateTime(timezone=True), nullable=True)
    scored_at: datetime = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    post = relationship("Post", back_populates="lead")
    feedbacks = relationship("Feedback", back_populates="lead")

    __table_args__ = (
        UniqueConstraint("post_id", name="uq_lead_post_id"),
    )


class Feedback(Base):
    """Human feedback on lead quality — used for scoring calibration."""

    __tablename__ = "feedback"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    lead_id: str = Column(UUID(as_uuid=False), ForeignKey("leads.id"), nullable=False, index=True)
    rating: int = Column(Integer, nullable=False)          # 1–5 stars
    label: str = Column(String(32), nullable=True)         # good | bad | duplicate
    reviewer: str = Column(String(128), nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)

    lead = relationship("Lead", back_populates="feedbacks")


class QuotaUsage(Base):
    """Gemini API token usage per calendar day for rate-limit tracking."""

    __tablename__ = "quota_usage"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    date: str = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    model: str = Column(String(64), nullable=False)
    tokens_used: int = Column(Integer, default=0, nullable=False)
    requests_count: int = Column(Integer, default=0, nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "model", name="uq_quota_date_model"),
    )


class UserProfile(Base):
    """
    Singleton user profile — stores the ICP, operation mode, and learned preferences.
    Convention: always use id=1 (single user, no auth yet).

    mode choices:
      b2b_sales    — find companies with buying intent for your product
      hiring       — find fast-growing companies that are actively hiring
      job_search   — find open positions matching your skills
      opportunity  — detect emerging market gaps and rising demand
    """

    __tablename__ = "user_profiles"

    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Operational context ───────────────────────────────────────────────────
    mode: str = Column(String(32), default="b2b_sales", nullable=False)
    product_description: str = Column(Text, nullable=True)        # "We build async video tools"
    target_customer: str = Column(Text, nullable=True)            # "Engineering managers at Series A startups"

    # ── Adaptive filters (JSONB arrays) ───────────────────────────────────────
    target_industries: list = Column(JSONB, nullable=False, default=list)       # ["saas", "fintech"]
    target_company_sizes: list = Column(JSONB, nullable=False, default=list)    # ["startup", "smb"]
    include_keywords: list = Column(JSONB, nullable=False, default=list)        # ["async", "remote"]
    exclude_keywords: list = Column(JSONB, nullable=False, default=list)        # ["enterprise", "legacy"]

    # ── Mode-specific preferences ─────────────────────────────────────────────
    hiring_roles: list = Column(JSONB, nullable=False, default=list)            # for hiring mode
    skills: list = Column(JSONB, nullable=False, default=list)                  # for job_search mode
    min_salary: int = Column(Integer, default=0, nullable=False)
    remote_only: bool = Column(Boolean, default=False, nullable=False)

    # ── Learned weights from feedback (JSONB dict) ────────────────────────────
    feedback_adjustments: dict = Column(JSONB, nullable=False, default=dict)    # "{industry}:{intent}" → float

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: datetime = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
