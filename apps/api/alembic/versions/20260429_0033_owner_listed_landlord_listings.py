"""allow landlord-owned listing publication

Revision ID: 20260429_0033
Revises: 20260428_0032
Create Date: 2026-04-29 10:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260429_0033"
down_revision = "20260428_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("listings", schema=None) as batch_op:
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )
        batch_op.add_column(sa.Column("owner_landlord_user_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_listings_owner_landlord_user_id",
            ["owner_landlord_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_listings_owner_landlord_user_id_users",
            "users",
            ["owner_landlord_user_id"],
            ["id"],
        )
        batch_op.create_check_constraint(
            "ck_listings_single_manager",
            "(organization_id IS NOT NULL AND owner_landlord_user_id IS NULL) "
            "OR (organization_id IS NULL AND owner_landlord_user_id IS NOT NULL)",
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM listing_applications "
        "WHERE listing_id IN (SELECT id FROM listings WHERE organization_id IS NULL)"
    )
    op.execute(
        "DELETE FROM trust_events "
        "WHERE listing_id IN (SELECT id FROM listings WHERE organization_id IS NULL)"
    )
    op.execute("DELETE FROM listings WHERE organization_id IS NULL")

    with op.batch_alter_table("listings", schema=None) as batch_op:
        batch_op.drop_constraint("ck_listings_single_manager", type_="check")
        batch_op.drop_constraint(
            "fk_listings_owner_landlord_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_listings_owner_landlord_user_id")
        batch_op.drop_column("owner_landlord_user_id")
        batch_op.alter_column(
            "organization_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
