"""add landlord owner assignment to properties

Revision ID: 20260428_0032
Revises: 20260427_0031
Create Date: 2026-04-28 14:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260428_0032"
down_revision = "20260427_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_landlord_user_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_properties_owner_landlord_user_id",
            ["owner_landlord_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_properties_owner_landlord_user_id_users",
            "users",
            ["owner_landlord_user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_properties_owner_landlord_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_properties_owner_landlord_user_id")
        batch_op.drop_column("owner_landlord_user_id")
