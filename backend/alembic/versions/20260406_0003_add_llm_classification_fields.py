"""20260406_0003_add_llm_classification_fields — Add missing LLM classification columns to leads.

Revision ID: 20260406_0003
Revises: 20260327_0002_user_profiles
Create Date: 2026-04-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

revision     = "20260406_0003"
down_revision = "20260404_120000"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # Add Evidence Trail columns (Amodei Safety)
    op.add_column("leads", sa.Column("pain_point", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("raw_excerpt", sa.Text(), nullable=True))

    # Add India Market Signals column (Lead-iq Moat)
    op.add_column("leads", sa.Column("india_signals", ARRAY(sa.String()), nullable=True, server_default="{}"))


def downgrade() -> None:
    op.drop_column("leads", "india_signals")
    op.drop_column("leads", "raw_excerpt")
    op.drop_column("leads", "pain_point")
