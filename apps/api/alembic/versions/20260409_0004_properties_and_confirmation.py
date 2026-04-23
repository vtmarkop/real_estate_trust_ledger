"""Add reusable properties and tenancy confirmation

Revision ID: 20260409_0004
Revises: 20260409_0003
Create Date: 2026-04-09 02:15:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0004"
down_revision: Union[str, Sequence[str], None] = "20260409_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'tenancy:counterparty_confirmed'")

    op.create_table(
        "properties",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_label", sa.String(length=255), nullable=False),
        sa.Column("address_line1", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_properties_created_by_user_id", "properties", ["created_by_user_id"], unique=False)

    with op.batch_alter_table(
        "tenancies",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.add_column(sa.Column("property_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("counterparty_confirmed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("counterparty_confirmed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tenancies_property_id_properties",
            "properties",
            ["property_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_tenancies_counterparty_confirmed_by_user_id_users",
            "users",
            ["counterparty_confirmed_by_user_id"],
            ["id"],
        )
        batch_op.create_index("ix_tenancies_property_id", ["property_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "tenancies",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_tenancies_property_id")
        batch_op.drop_constraint("fk_tenancies_counterparty_confirmed_by_user_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_tenancies_property_id_properties", type_="foreignkey")
        batch_op.drop_column("counterparty_confirmed_by_user_id")
        batch_op.drop_column("counterparty_confirmed_at")
        batch_op.drop_column("property_id")
    op.drop_index("ix_properties_created_by_user_id", table_name="properties")
    op.drop_table("properties")
