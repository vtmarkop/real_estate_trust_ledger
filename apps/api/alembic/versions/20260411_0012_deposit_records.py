"""Add deposit records and trust-event deposit linkage

Revision ID: 20260411_0012
Revises: 20260411_0011
Create Date: 2026-04-11 03:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0012"
down_revision: Union[str, Sequence[str], None] = "20260411_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deposit_records",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenancy_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("counterparty_action_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("held_amount_minor", sa.Integer(), nullable=False),
        sa.Column("proposed_return_minor", sa.Integer(), nullable=False),
        sa.Column("withheld_amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("deposit_status", sa.String(length=32), nullable=False),
        sa.Column("move_out_date", sa.Date(), nullable=True),
        sa.Column("return_due_date", sa.Date(), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settlement_artifact_name", sa.String(length=255), nullable=True),
        sa.Column("settlement_summary", sa.String(length=1000), nullable=True),
        sa.Column("settlement_notes", sa.String(length=1000), nullable=True),
        sa.Column("dispute_notes", sa.String(length=1000), nullable=True),
        sa.Column("counterparty_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["counterparty_action_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenancy_id", name="uq_deposit_records_tenancy_id"),
    )
    op.create_index("ix_deposit_records_tenancy_id", "deposit_records", ["tenancy_id"], unique=False)
    op.create_index(
        "ix_deposit_records_created_by_user_id",
        "deposit_records",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_deposit_records_counterparty_action_by_user_id",
        "deposit_records",
        ["counterparty_action_by_user_id"],
        unique=False,
    )

    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("deposit_record_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_deposit_record_id",
            "deposit_records",
            ["deposit_record_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_deposit_record_id",
            ["deposit_record_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.drop_index("ix_trust_events_deposit_record_id")
        batch_op.drop_constraint("fk_trust_events_deposit_record_id", type_="foreignkey")
        batch_op.drop_column("deposit_record_id")

    op.drop_index(
        "ix_deposit_records_counterparty_action_by_user_id",
        table_name="deposit_records",
    )
    op.drop_index("ix_deposit_records_created_by_user_id", table_name="deposit_records")
    op.drop_index("ix_deposit_records_tenancy_id", table_name="deposit_records")
    op.drop_table("deposit_records")
