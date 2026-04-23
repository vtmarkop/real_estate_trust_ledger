"""Add history imports for cold-start onboarding

Revision ID: 20260410_0007
Revises: 20260410_0006
Create Date: 2026-04-10 01:40:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0007"
down_revision: Union[str, Sequence[str], None] = "20260410_0006"
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
    "listing:published",
    "application:submitted",
    "application:status_updated",
    name="trusteventtype",
)
history_import_status_enum = sa.Enum(
    "draft",
    "submitted",
    "accepted",
    "rejected",
    name="historyimportstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'history_import:submitted'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'history_import:accepted'")
        op.execute("ALTER TYPE trusteventtype ADD VALUE IF NOT EXISTS 'history_import:rejected'")

    op.create_table(
        "history_imports",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=True),
        sa.Column("status", history_import_status_enum, nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_notes", sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_history_imports_subject_user_id",
        "history_imports",
        ["subject_user_id"],
        unique=False,
    )

    with op.batch_alter_table(
        "tenancies",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.add_column(sa.Column("history_import_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_tenancies_history_import_id_history_imports",
            "history_imports",
            ["history_import_id"],
            ["id"],
        )
        batch_op.create_index("ix_tenancies_history_import_id", ["history_import_id"], unique=False)

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
        batch_op.add_column(sa.Column("history_import_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_history_import_id_history_imports",
            "history_imports",
            ["history_import_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_history_import_id",
            ["history_import_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_events",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_trust_events_history_import_id")
        batch_op.drop_constraint(
            "fk_trust_events_history_import_id_history_imports",
            type_="foreignkey",
        )
        batch_op.drop_column("history_import_id")
        if bind.dialect.name != "postgresql":
            batch_op.alter_column(
                "event_type",
                existing_type=new_trust_event_type_enum,
                type_=old_trust_event_type_enum,
                existing_nullable=False,
            )

    with op.batch_alter_table(
        "tenancies",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_tenancies_history_import_id")
        batch_op.drop_constraint(
            "fk_tenancies_history_import_id_history_imports",
            type_="foreignkey",
        )
        batch_op.drop_column("history_import_id")

    op.drop_index("ix_history_imports_subject_user_id", table_name="history_imports")
    op.drop_table("history_imports")

    history_import_status_enum.drop(op.get_bind(), checkfirst=True)
