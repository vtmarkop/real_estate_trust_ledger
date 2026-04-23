"""Add trust score recalculation request and batch tables

Revision ID: 20260411_0010
Revises: 20260410_0009
Create Date: 2026-04-11 00:40:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0010"
down_revision: Union[str, Sequence[str], None] = "20260410_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trust_score_recalculation_batches",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("scope_type", sa.String(length=50), nullable=False),
        sa.Column("calculation_reason", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_user_count", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trust_score_recalculation_batches_requested_by_user_id",
        "trust_score_recalculation_batches",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_trust_score_recalculation_batches_organization_id",
        "trust_score_recalculation_batches",
        ["organization_id"],
        unique=False,
    )

    op.create_table(
        "trust_score_recalculation_requests",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("calculation_reason", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("result_tenant_score", sa.Integer(), nullable=True),
        sa.Column("result_landlord_score", sa.Integer(), nullable=True),
        sa.Column("result_verification_strength", sa.Integer(), nullable=True),
        sa.Column("result_scoring_version", sa.String(length=32), nullable=True),
        sa.Column("result_calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["trust_score_recalculation_batches.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trust_score_recalculation_requests_user_id",
        "trust_score_recalculation_requests",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_trust_score_recalculation_requests_batch_id",
        "trust_score_recalculation_requests",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        "ix_trust_score_recalculation_requests_requested_by_user_id",
        "trust_score_recalculation_requests",
        ["requested_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trust_score_recalculation_requests_requested_by_user_id",
        table_name="trust_score_recalculation_requests",
    )
    op.drop_index(
        "ix_trust_score_recalculation_requests_batch_id",
        table_name="trust_score_recalculation_requests",
    )
    op.drop_index(
        "ix_trust_score_recalculation_requests_user_id",
        table_name="trust_score_recalculation_requests",
    )
    op.drop_table("trust_score_recalculation_requests")

    op.drop_index(
        "ix_trust_score_recalculation_batches_organization_id",
        table_name="trust_score_recalculation_batches",
    )
    op.drop_index(
        "ix_trust_score_recalculation_batches_requested_by_user_id",
        table_name="trust_score_recalculation_batches",
    )
    op.drop_table("trust_score_recalculation_batches")
