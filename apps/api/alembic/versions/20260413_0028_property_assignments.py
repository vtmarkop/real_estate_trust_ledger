"""add property assignment fields for agency and tenant workflows

Revision ID: 20260413_0028
Revises: 20260413_0027
Create Date: 2026-04-13 18:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0028"
down_revision = "20260413_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(sa.Column("assigned_agency_organization_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("assigned_agency_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("assigned_tenant_user_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_properties_assigned_agency_organization_id",
            ["assigned_agency_organization_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_properties_assigned_agency_user_id",
            ["assigned_agency_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_properties_assigned_tenant_user_id",
            ["assigned_tenant_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_properties_assigned_agency_organization_id_organizations",
            "organizations",
            ["assigned_agency_organization_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_properties_assigned_agency_user_id_users",
            "users",
            ["assigned_agency_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_properties_assigned_tenant_user_id_users",
            "users",
            ["assigned_tenant_user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_properties_assigned_tenant_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_properties_assigned_agency_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_properties_assigned_agency_organization_id_organizations",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_properties_assigned_tenant_user_id")
        batch_op.drop_index("ix_properties_assigned_agency_user_id")
        batch_op.drop_index("ix_properties_assigned_agency_organization_id")
        batch_op.drop_column("assigned_tenant_user_id")
        batch_op.drop_column("assigned_agency_user_id")
        batch_op.drop_column("assigned_agency_organization_id")
