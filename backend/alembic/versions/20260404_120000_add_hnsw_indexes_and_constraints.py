"""Add HNSW vector index, composite indexes, CHECK constraints

Revision ID: 20260404_120000
Revises: 20260404_0003
Create Date: 2026-04-04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260404_120000"
down_revision = "20260404_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Install pgvector if not installed
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column if missing (in case migration 0003 failed)
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='leads' AND column_name='embedding'
            ) THEN
                ALTER TABLE leads ADD COLUMN embedding vector(768);
            END IF;
        END $$
    ''')

    # HNSW index — better than IVFFlat for most use cases
    op.execute('''
        CREATE INDEX CONCURRENTLY IF NOT EXISTS leads_embedding_hnsw_idx
        ON leads USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')

    # Composite indexes for dashboard query patterns
    op.execute('''
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lead_status_created
        ON leads (status, created_at DESC)
    ''')
    op.execute('''
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lead_icp_status
        ON leads (icp_score DESC, status)
        WHERE icp_score IS NOT NULL
    ''')
    op.execute('''
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lead_source_created
        ON leads (source, created_at DESC)
    ''')
    op.execute('''
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_lead_final_score
        ON leads (final_score DESC)
        WHERE final_score IS NOT NULL
    ''')

    # CHECK constraints
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_lead_confidence_range'
            ) THEN
                ALTER TABLE leads
                ADD CONSTRAINT ck_lead_confidence_range
                CHECK (confidence >= 0.0 AND confidence <= 1.0);
            END IF;
        END $$
    ''')
    op.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_lead_icp_score_range'
            ) THEN
                ALTER TABLE leads
                ADD CONSTRAINT ck_lead_icp_score_range
                CHECK (icp_score IS NULL OR
                       (icp_score >= 0.0 AND icp_score <= 1.0));
            END IF;
        END $$
    ''')


def downgrade() -> None:
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS leads_embedding_hnsw_idx")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_lead_status_created")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_lead_icp_status")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_lead_source_created")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_lead_final_score")
    op.execute("ALTER TABLE leads DROP CONSTRAINT IF EXISTS ck_lead_confidence_range")
    op.execute("ALTER TABLE leads DROP CONSTRAINT IF EXISTS ck_lead_icp_score_range")
