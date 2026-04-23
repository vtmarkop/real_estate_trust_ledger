"""add explicit property management mode

Revision ID: 20260413_0030
Revises: 20260413_0029
Create Date: 2026-04-13 23:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0030"
down_revision = "20260413_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "management_mode",
                sa.String(length=32),
                nullable=False,
                server_default="owner_managed",
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE properties
            SET management_mode = 'agency_managed'
            WHERE assigned_agency_organization_id IS NOT NULL
               OR assigned_agency_user_id IS NOT NULL
            """
        )
    )

    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.alter_column("management_mode", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_column("management_mode")
