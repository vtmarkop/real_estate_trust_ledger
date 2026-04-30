"""link accepted applications to created tenancies

Revision ID: 20260429_0034
Revises: 20260429_0033
Create Date: 2026-04-29 13:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260429_0034"
down_revision = "20260429_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("listing_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tenancy_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_listing_applications_tenancy_id",
            ["tenancy_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_listing_applications_tenancy_id_tenancies",
            "tenancies",
            ["tenancy_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("listing_applications", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_listing_applications_tenancy_id_tenancies",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_listing_applications_tenancy_id")
        batch_op.drop_column("tenancy_id")
