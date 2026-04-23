"""Add payment records and trust-event payment linkage

Revision ID: 20260411_0011
Revises: 20260411_0010
Create Date: 2026-04-11 02:15:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0011"
down_revision: Union[str, Sequence[str], None] = "20260411_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_records",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenancy_id", sa.Uuid(), nullable=False),
        sa.Column("payer_user_id", sa.Uuid(), nullable=False),
        sa.Column("payee_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("counterparty_action_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("payment_type", sa.String(length=50), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("proof_status", sa.String(length=32), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("period_start_date", sa.Date(), nullable=True),
        sa.Column("period_end_date", sa.Date(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof_artifact_name", sa.String(length=255), nullable=True),
        sa.Column("proof_summary", sa.String(length=1000), nullable=True),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("counterparty_notes", sa.String(length=1000), nullable=True),
        sa.Column("counterparty_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["counterparty_action_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["payee_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["payer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_records_tenancy_id", "payment_records", ["tenancy_id"], unique=False)
    op.create_index("ix_payment_records_payer_user_id", "payment_records", ["payer_user_id"], unique=False)
    op.create_index("ix_payment_records_payee_user_id", "payment_records", ["payee_user_id"], unique=False)
    op.create_index(
        "ix_payment_records_created_by_user_id",
        "payment_records",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_records_counterparty_action_by_user_id",
        "payment_records",
        ["counterparty_action_by_user_id"],
        unique=False,
    )

    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("payment_record_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_payment_record_id",
            "payment_records",
            ["payment_record_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_payment_record_id",
            ["payment_record_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.drop_index("ix_trust_events_payment_record_id")
        batch_op.drop_constraint("fk_trust_events_payment_record_id", type_="foreignkey")
        batch_op.drop_column("payment_record_id")

    op.drop_index(
        "ix_payment_records_counterparty_action_by_user_id",
        table_name="payment_records",
    )
    op.drop_index("ix_payment_records_created_by_user_id", table_name="payment_records")
    op.drop_index("ix_payment_records_payee_user_id", table_name="payment_records")
    op.drop_index("ix_payment_records_payer_user_id", table_name="payment_records")
    op.drop_index("ix_payment_records_tenancy_id", table_name="payment_records")
    op.drop_table("payment_records")
