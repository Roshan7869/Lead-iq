"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel
from datetime import datetime


class LeadBase(BaseModel):
    id: str
    name: str
    company: str | None = None
    title: str | None = None
    stage: str = "detected"
    source: str | None = None
    priority: str = "cold"
    signal: str | None = None
    estimated_value: float = 0
    email: str | None = None
    linkedin_url: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    detected_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class LeadScoreSchema(BaseModel):
    lead_id: str
    intent: float
    urgency: float
    budget: float
    score: int
    scored_at: datetime

    class Config:
        from_attributes = True


class OutreachDraftSchema(BaseModel):
    lead_id: str
    linkedin: str | None = None
    email: str | None = None
    whatsapp: str | None = None
    strategy: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadEvent(BaseModel):
    """Schema for lead:collected stream events"""
    id: str
    text: str
    source: str
    timestamp: str


class AnalyzedEvent(BaseModel):
    """Schema for lead:analyzed stream events"""
    intent: float
    urgency: float
    budget: float
    category: str
