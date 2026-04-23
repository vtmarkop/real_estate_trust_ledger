"""Add trust score snapshot and history tables

Revision ID: 20260410_0009
Revises: 20260410_0008
Create Date: 2026-04-10 04:35:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0009"
down_revision: Union[str, Sequence[str], None] = "20260410_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trust_score_snapshots",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_score", sa.Integer(), nullable=False),
        sa.Column("landlord_score", sa.Integer(), nullable=False),
        sa.Column("verification_strength", sa.Integer(), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_trust_score_snapshots_user_id",
        "trust_score_snapshots",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "trust_score_history",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_score", sa.Integer(), nullable=False),
        sa.Column("landlord_score", sa.Integer(), nullable=False),
        sa.Column("verification_strength", sa.Integer(), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("calculation_reason", sa.String(length=100), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trust_score_history_user_id",
        "trust_score_history",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_trust_score_history_user_id", table_name="trust_score_history")
    op.drop_table("trust_score_history")
    op.drop_index("ix_trust_score_snapshots_user_id", table_name="trust_score_snapshots")
    op.drop_table("trust_score_snapshots")
