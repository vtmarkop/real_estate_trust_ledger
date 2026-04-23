"""Add evidence documents and review workflow

Revision ID: 20260410_0006
Revises: 20260409_0005
Create Date: 2026-04-10 00:45:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0006"
down_revision: Union[str, Sequence[str], None] = "20260409_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:counterparty_confirmed",
    "tenancy:review_requested",
    "tenancy:reviewed",
    "listing:published",
    "application:submitted",
    "application:status_updated",
    name="trusteventtype",
)
new_trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:counterparty_confirmed",
    "tenancy:review_requested",
    "tenancy:reviewed",
    "evidence:submitted",
    "evidence:accepted",
    "evidence:rejected",
    "listing:published",
    "application:submitted",
    "application:status_updated",
    name="trusteventtype",
)
evidence_document_type_enum = sa.Enum(
    "lease_agreement",
    "rent_receipt",
    "utility_settlement",
    "deposit_return",
    "landlord_reference",
    "identity_document",
    "other",
    name="evidencedocumenttype",
)
evidence_review_status_enum = sa.Enum(
    "submitted",
    "accepted",
    "rejected",
    name="evidencereviewstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'evidence:submitted'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'evidence:accepted'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'evidence:rejected'")

    op.create_table(
        "evidence_documents",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenancy_id", sa.Uuid(), nullable=False),
        sa.Column("subject_user_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", evidence_document_type_enum, nullable=False),
        sa.Column("review_status", evidence_review_status_enum, nullable=False),
        sa.Column("artifact_name", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False),
        sa.Column("issuer_name", sa.String(length=255), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("review_requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_notes", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evidence_documents_tenancy_id",
        "evidence_documents",
        ["tenancy_id"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_documents_subject_user_id",
        "evidence_documents",
        ["subject_user_id"],
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
        batch_op.add_column(sa.Column("evidence_document_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_evidence_document_id_evidence_documents",
            "evidence_documents",
            ["evidence_document_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_evidence_document_id",
            ["evidence_document_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_events",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_trust_events_evidence_document_id")
        batch_op.drop_constraint(
            "fk_trust_events_evidence_document_id_evidence_documents",
            type_="foreignkey",
        )
        batch_op.drop_column("evidence_document_id")
        if bind.dialect.name != "postgresql":
            batch_op.alter_column(
                "event_type",
                existing_type=new_trust_event_type_enum,
                type_=old_trust_event_type_enum,
                existing_nullable=False,
            )

    op.drop_index("ix_evidence_documents_subject_user_id", table_name="evidence_documents")
    op.drop_index("ix_evidence_documents_tenancy_id", table_name="evidence_documents")
    op.drop_table("evidence_documents")

    evidence_review_status_enum.drop(op.get_bind(), checkfirst=True)
    evidence_document_type_enum.drop(op.get_bind(), checkfirst=True)
