"""Database models — Phase 8 (PostgreSQL / SQLAlchemy)"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    title = Column(String, nullable=True)
    stage = Column(String, default="detected")
    source = Column(String, nullable=True)
    priority = Column(String, default="cold")
    signal = Column(Text, nullable=True)
    estimated_value = Column(Float, default=0)
    email = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    detected_at = Column(DateTime(timezone=True), default=_now)
    last_activity = Column(DateTime(timezone=True), default=_now)


class LeadScoreModel(Base):
    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String, index=True, nullable=False)
    intent = Column(Float, default=0)
    urgency = Column(Float, default=0)
    budget = Column(Float, default=0)
    score = Column(Integer, default=0)
    scored_at = Column(DateTime(timezone=True), default=_now)


class OutreachDraftModel(Base):
    __tablename__ = "outreach_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String, index=True, nullable=False)
    linkedin = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    whatsapp = Column(Text, nullable=True)
    strategy = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
