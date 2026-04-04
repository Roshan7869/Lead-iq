"""
backend/models/lead.py — Lead SQLAlchemy Model

Core lead model with embedding column for pgvector semantic search.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

# pgvector import (will fail gracefully if not installed)
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None

from backend.shared.db import Base

if TYPE_CHECKING:
    from backend.models.lead_event import LeadEvent


class LeadStage(str, PyEnum):
    """Lead pipeline stages."""

    detected = "detected"
    qualified = "qualified"
    contacted = "contacted"
    meeting = "meeting"
    closed = "closed"


class LeadPriority(str, PyEnum):
    """Lead priority levels."""

    hot = "hot"
    warm = "warm"
    cold = "cold"


class Lead(Base):
    """
    Lead — Core lead model for B2B intelligence.

    Attributes:
        id: UUID primary key
        company_name: Company or organization name
        industry: Business sector
        location: City, State, Country
        company_size: Employee count range
        funding_stage: Current funding stage
        funding_amount: Total funding in USD
        tech_stack: Technologies used (array)
        email: Contact email
        linkedin_url: LinkedIn profile URL
        website: Company website
        founded_year: Year founded
        title: Contact title/role
        intent_signals: Buying intent indicators (JSONB)
        confidence: Extraction confidence score (0-1)
        source: Data source identifier
        source_url: Original URL where lead was found
        stage: Pipeline stage
        priority: Hot/warm/cold priority
        embedding: 768-dim vector for semantic search
        created_at: Record creation timestamp
        updated_at: Record update timestamp

    Indexes:
        - ix_leads_email: Unique email lookup
        - ix_leads_linkedin: Unique LinkedIn lookup
        - ix_leads_company_domain: Company domain lookup
        - ix_leads_stage: Pipeline filtering
        - ix_leads_confidence: Quality filtering
        - ix_leads_embedding: Vector similarity search
    """

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company information
    company_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)  # 1-10/11-50/51-200/201-500/500+
    company_domain = Column(String(255), nullable=True, index=True)

    # Funding information
    funding_stage = Column(String(50), nullable=True)  # seed/series-a/series-b/etc
    funding_amount = Column(Integer, nullable=True)  # Total funding in USD
    founded_year = Column(Integer, nullable=True)

    # Contact information
    email = Column(String(255), nullable=True, index=True)
    linkedin_url = Column(String(512), nullable=True, index=True)
    website = Column(String(512), nullable=True)
    phone = Column(String(50), nullable=True)

    # Role information
    title = Column(String(255), nullable=True)

    # Technical information
    tech_stack = Column(ARRAY(String), nullable=True)

    # Intent and scoring
    intent_signals = Column(JSONB, nullable=True, default=list)
    confidence = Column(Float, nullable=False, default=0.0)
    icp_score = Column(Float, nullable=True)  # ICP fit score (0-100)

    # Source tracking
    source = Column(String(100), nullable=False, index=True)  # tracxn/github/etc
    source_url = Column(Text, nullable=True)
    source_actor = Column(String(100), nullable=True)  # Actor that collected this

    # Pipeline state
    stage = Column(
        Enum(LeadStage, name="lead_stage"),
        nullable=False,
        default=LeadStage.detected,
        index=True,
    )
    priority = Column(
        Enum(LeadPriority, name="lead_priority"),
        nullable=True,
        index=True,
    )

    # Embedding for semantic search (768-dim)
    embedding = Column(Vector(768), nullable=True) if HAS_PGVECTOR else Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_leads_email", "email"),
        Index("ix_leads_linkedin", "linkedin_url"),
        Index("ix_leads_company_domain", "company_domain"),
        Index("ix_leads_stage", "stage"),
        Index("ix_leads_confidence", "confidence"),
        Index("ix_leads_source", "source"),
        Index("ix_leads_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, company={self.company_name}, stage={self.stage})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "company_name": self.company_name,
            "industry": self.industry,
            "location": self.location,
            "company_size": self.company_size,
            "company_domain": self.company_domain,
            "funding_stage": self.funding_stage,
            "funding_amount": self.funding_amount,
            "founded_year": self.founded_year,
            "email": self.email,
            "linkedin_url": self.linkedin_url,
            "website": self.website,
            "phone": self.phone,
            "title": self.title,
            "tech_stack": self.tech_stack,
            "intent_signals": self.intent_signals,
            "confidence": self.confidence,
            "icp_score": self.icp_score,
            "source": self.source,
            "source_url": self.source_url,
            "stage": self.stage.value if self.stage else None,
            "priority": self.priority.value if self.priority else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }