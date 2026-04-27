"""add explicit user workspace roles

Revision ID: 20260427_0031
Revises: 20260413_0030
Create Date: 2026-04-27 14:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260427_0031"
down_revision = "20260413_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "workspace_roles_json",
                sa.Text(),
                nullable=False,
                server_default='["tenant"]',
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET workspace_roles_json = CASE
                WHEN system_role IN ('admin', 'reviewer') THEN '["internal"]'
                ELSE '["tenant"]'
            END
            """
        )
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("workspace_roles_json", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("workspace_roles_json")
