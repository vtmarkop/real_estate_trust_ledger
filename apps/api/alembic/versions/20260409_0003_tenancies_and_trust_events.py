"""Add tenancies and trust events

Revision ID: 20260409_0003
Revises: 20260409_0002
Create Date: 2026-04-09 01:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0003"
down_revision: Union[str, Sequence[str], None] = "20260409_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


tenancy_status_enum = sa.Enum(
    "active",
    "ended",
    "cancelled",
    name="tenancystatus",
)
verification_status_enum = sa.Enum(
    "self_reported",
    "counterparty_confirmed",
    "reviewed",
    "verified",
    name="verificationstatus",
)
trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:review_requested",
    "tenancy:reviewed",
    name="trusteventtype",
)


def upgrade() -> None:
    op.create_table(
        "tenancies",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("property_label", sa.String(length=255), nullable=False),
        sa.Column("address_line1", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("tenancy_status", tenancy_status_enum, nullable=False),
        sa.Column("verification_status", verification_status_enum, nullable=False),
        sa.Column("lease_start_date", sa.Date(), nullable=False),
        sa.Column("lease_end_date", sa.Date(), nullable=True),
        sa.Column("monthly_rent_minor", sa.Integer(), nullable=False),
        sa.Column("deposit_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("tenant_user_id", sa.Uuid(), nullable=False),
        sa.Column("landlord_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("review_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_notes", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["landlord_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenancies_tenant_user_id", "tenancies", ["tenant_user_id"], unique=False)
    op.create_index(
        "ix_tenancies_landlord_user_id",
        "tenancies",
        ["landlord_user_id"],
        unique=False,
    )

    op.create_table(
        "trust_events",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_user_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("tenancy_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", trust_event_type_enum, nullable=False),
        sa.Column("verification_status", verification_status_enum, nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trust_events_subject_user_id", "trust_events", ["subject_user_id"], unique=False)
    op.create_index("ix_trust_events_tenancy_id", "trust_events", ["tenancy_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trust_events_tenancy_id", table_name="trust_events")
    op.drop_index("ix_trust_events_subject_user_id", table_name="trust_events")
    op.drop_table("trust_events")
    op.drop_index("ix_tenancies_landlord_user_id", table_name="tenancies")
    op.drop_index("ix_tenancies_tenant_user_id", table_name="tenancies")
    op.drop_table("tenancies")

    trust_event_type_enum.drop(op.get_bind(), checkfirst=True)
    verification_status_enum.drop(op.get_bind(), checkfirst=True)
    tenancy_status_enum.drop(op.get_bind(), checkfirst=True)
