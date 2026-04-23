"""Add listings and applications

Revision ID: 20260409_0005
Revises: 20260409_0004
Create Date: 2026-04-09 03:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0005"
down_revision: Union[str, Sequence[str], None] = "20260409_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:counterparty_confirmed",
    "tenancy:review_requested",
    "tenancy:reviewed",
    name="trusteventtype",
)
new_trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:counterparty_confirmed",
    "tenancy:review_requested",
    "tenancy:reviewed",
    "listing:published",
    "application:submitted",
    "application:status_updated",
    name="trusteventtype",
)
listing_status_enum = sa.Enum("open", "paused", "closed", name="listingstatus")
application_status_enum = sa.Enum(
    "submitted",
    "under_review",
    "accepted",
    "rejected",
    "withdrawn",
    name="applicationstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'listing:published'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'application:submitted'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'application:status_updated'")

    op.create_table(
        "listings",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("listing_status", listing_status_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("monthly_rent_minor", sa.Integer(), nullable=False),
        sa.Column("deposit_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column(
            "minimum_counterparty_confirmed_tenancies",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("minimum_verified_tenancies", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listings_organization_id", "listings", ["organization_id"], unique=False)
    op.create_index("ix_listings_property_id", "listings", ["property_id"], unique=False)

    op.create_table(
        "listing_applications",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("applicant_user_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("application_status", application_status_enum, nullable=False),
        sa.Column("eligibility_met", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("eligibility_notes", sa.String(length=500), nullable=True),
        sa.Column("applicant_note", sa.String(length=1000), nullable=True),
        sa.Column("status_notes", sa.String(length=1000), nullable=True),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["applicant_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_id", "applicant_user_id", name="uq_listing_applications_listing_applicant"),
    )
    op.create_index(
        "ix_listing_applications_listing_id",
        "listing_applications",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_listing_applications_applicant_user_id",
        "listing_applications",
        ["applicant_user_id"],
        unique=False,
    )

    with op.batch_alter_table(
        "trust_events",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        if bind.dialect.name != "postgresql":
            batch_op.alter_column(
                "event_type",
                existing_type=old_trust_event_type_enum,
                type_=new_trust_event_type_enum,
                existing_nullable=False,
            )
        batch_op.add_column(sa.Column("listing_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_listing_id_listings",
            "listings",
            ["listing_id"],
            ["id"],
        )
        batch_op.create_index("ix_trust_events_listing_id", ["listing_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_events",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_trust_events_listing_id")
        batch_op.drop_constraint("fk_trust_events_listing_id_listings", type_="foreignkey")
        batch_op.drop_column("listing_id")
        if bind.dialect.name != "postgresql":
            batch_op.alter_column(
                "event_type",
                existing_type=new_trust_event_type_enum,
                type_=old_trust_event_type_enum,
                existing_nullable=False,
            )

    op.drop_index("ix_listing_applications_applicant_user_id", table_name="listing_applications")
    op.drop_index("ix_listing_applications_listing_id", table_name="listing_applications")
    op.drop_table("listing_applications")
    op.drop_index("ix_listings_property_id", table_name="listings")
    op.drop_index("ix_listings_organization_id", table_name="listings")
    op.drop_table("listings")

    application_status_enum.drop(op.get_bind(), checkfirst=True)
    listing_status_enum.drop(op.get_bind(), checkfirst=True)
