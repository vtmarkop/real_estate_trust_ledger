"""Add counterparty reference requests

Revision ID: 20260410_0008
Revises: 20260410_0007
Create Date: 2026-04-10 03:05:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0008"
down_revision: Union[str, Sequence[str], None] = "20260410_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


old_trust_event_type_enum = sa.Enum(
    "tenancy:created",
    "tenancy:counterparty_confirmed",
    "tenancy:review_requested",
    "tenancy:reviewed",
    "evidence:submitted",
    "evidence:accepted",
    "evidence:rejected",
    "history_import:submitted",
    "history_import:accepted",
    "history_import:rejected",
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
    "history_import:submitted",
    "history_import:accepted",
    "history_import:rejected",
    "reference_request:created",
    "reference_request:fulfilled",
    "listing:published",
    "application:submitted",
    "application:status_updated",
    name="trusteventtype",
)
reference_request_status_enum = sa.Enum(
    "pending",
    "fulfilled",
    "declined",
    name="referencerequeststatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'reference_request:created'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'reference_request:fulfilled'")

    op.create_table(
        "reference_requests",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenancy_id", sa.Uuid(), nullable=False),
        sa.Column("subject_user_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("requested_from_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", reference_request_status_enum, nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_from_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reference_requests_tenancy_id",
        "reference_requests",
        ["tenancy_id"],
        unique=False,
    )
    op.create_index(
        "ix_reference_requests_subject_user_id",
        "reference_requests",
        ["subject_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_reference_requests_requested_from_user_id",
        "reference_requests",
        ["requested_from_user_id"],
        unique=False,
    )

    with op.batch_alter_table(
        "evidence_documents",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.add_column(sa.Column("reference_request_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_evidence_documents_reference_request_id_reference_requests",
            "reference_requests",
            ["reference_request_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_evidence_documents_reference_request_id",
            ["reference_request_id"],
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
        batch_op.add_column(sa.Column("reference_request_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_reference_request_id_reference_requests",
            "reference_requests",
            ["reference_request_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_reference_request_id",
            ["reference_request_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_events",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_trust_events_reference_request_id")
        batch_op.drop_constraint(
            "fk_trust_events_reference_request_id_reference_requests",
            type_="foreignkey",
        )
        batch_op.drop_column("reference_request_id")
        if bind.dialect.name != "postgresql":
            batch_op.alter_column(
                "event_type",
                existing_type=new_trust_event_type_enum,
                type_=old_trust_event_type_enum,
                existing_nullable=False,
            )

    with op.batch_alter_table(
        "evidence_documents",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_evidence_documents_reference_request_id",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_evidence_documents_reference_request_id_reference_requests",
            type_="foreignkey",
        )
        batch_op.drop_column("reference_request_id")

    op.drop_index(
        "ix_reference_requests_requested_from_user_id",
        table_name="reference_requests",
    )
    op.drop_index("ix_reference_requests_subject_user_id", table_name="reference_requests")
    op.drop_index("ix_reference_requests_tenancy_id", table_name="reference_requests")
    op.drop_table("reference_requests")

    reference_request_status_enum.drop(op.get_bind(), checkfirst=True)
