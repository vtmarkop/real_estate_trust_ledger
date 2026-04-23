"""add dispute verdict and appeal workflow fields

Revision ID: 20260413_0027
Revises: 20260412_0026
Create Date: 2026-04-13 11:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0027"
down_revision = "20260412_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment_records", schema=None) as batch_op:
        batch_op.add_column(sa.Column("disputed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("review_requested_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("appeal_requested_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("counterparty_stored_artifact_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("counterparty_artifact_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("dispute_notes", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("disputed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("review_requested_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("verdict_outcome", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("verdict_summary", sa.String(length=1000), nullable=True))
        batch_op.add_column(
            sa.Column("verdict_tenant_score_delta", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("verdict_landlord_score_delta", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("appeal_notes", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("appeal_requested_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_payment_records_disputed_by_user_id", ["disputed_by_user_id"], unique=False)
        batch_op.create_index(
            "ix_payment_records_review_requested_by_user_id",
            ["review_requested_by_user_id"],
            unique=False,
        )
        batch_op.create_index("ix_payment_records_reviewed_by_user_id", ["reviewed_by_user_id"], unique=False)
        batch_op.create_index(
            "ix_payment_records_appeal_requested_by_user_id",
            ["appeal_requested_by_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_payment_records_counterparty_stored_artifact_id",
            ["counterparty_stored_artifact_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_payment_records_disputed_by_user_id_users",
            "users",
            ["disputed_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_payment_records_review_requested_by_user_id_users",
            "users",
            ["review_requested_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_payment_records_reviewed_by_user_id_users",
            "users",
            ["reviewed_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_payment_records_appeal_requested_by_user_id_users",
            "users",
            ["appeal_requested_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_payment_records_counterparty_stored_artifact_id_stored_artifacts",
            "stored_artifacts",
            ["counterparty_stored_artifact_id"],
            ["id"],
        )

    with op.batch_alter_table("maintenance_tickets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("review_requested_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("appeal_requested_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("review_requested_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("verdict_outcome", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("verdict_summary", sa.String(length=1000), nullable=True))
        batch_op.add_column(
            sa.Column("verdict_tenant_score_delta", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("verdict_landlord_score_delta", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("appeal_notes", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("appeal_requested_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_maintenance_tickets_review_requested_by_user_id",
            ["review_requested_by_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_maintenance_tickets_reviewed_by_user_id",
            ["reviewed_by_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_maintenance_tickets_appeal_requested_by_user_id",
            ["appeal_requested_by_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_maintenance_tickets_review_requested_by_user_id_users",
            "users",
            ["review_requested_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_maintenance_tickets_reviewed_by_user_id_users",
            "users",
            ["reviewed_by_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_maintenance_tickets_appeal_requested_by_user_id_users",
            "users",
            ["appeal_requested_by_user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("maintenance_tickets", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_maintenance_tickets_appeal_requested_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_maintenance_tickets_reviewed_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_maintenance_tickets_review_requested_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_maintenance_tickets_appeal_requested_by_user_id")
        batch_op.drop_index("ix_maintenance_tickets_reviewed_by_user_id")
        batch_op.drop_index("ix_maintenance_tickets_review_requested_by_user_id")
        batch_op.drop_column("appeal_requested_at")
        batch_op.drop_column("appeal_notes")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("verdict_landlord_score_delta")
        batch_op.drop_column("verdict_tenant_score_delta")
        batch_op.drop_column("verdict_summary")
        batch_op.drop_column("verdict_outcome")
        batch_op.drop_column("review_requested_at")
        batch_op.drop_column("appeal_requested_by_user_id")
        batch_op.drop_column("reviewed_by_user_id")
        batch_op.drop_column("review_requested_by_user_id")

    with op.batch_alter_table("payment_records", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_payment_records_counterparty_stored_artifact_id_stored_artifacts",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_payment_records_appeal_requested_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_payment_records_reviewed_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_payment_records_review_requested_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_payment_records_disputed_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_payment_records_counterparty_stored_artifact_id")
        batch_op.drop_index("ix_payment_records_appeal_requested_by_user_id")
        batch_op.drop_index("ix_payment_records_reviewed_by_user_id")
        batch_op.drop_index("ix_payment_records_review_requested_by_user_id")
        batch_op.drop_index("ix_payment_records_disputed_by_user_id")
        batch_op.drop_column("appeal_requested_at")
        batch_op.drop_column("appeal_notes")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("verdict_landlord_score_delta")
        batch_op.drop_column("verdict_tenant_score_delta")
        batch_op.drop_column("verdict_summary")
        batch_op.drop_column("verdict_outcome")
        batch_op.drop_column("review_requested_at")
        batch_op.drop_column("disputed_at")
        batch_op.drop_column("dispute_notes")
        batch_op.drop_column("counterparty_artifact_name")
        batch_op.drop_column("counterparty_stored_artifact_id")
        batch_op.drop_column("appeal_requested_by_user_id")
        batch_op.drop_column("reviewed_by_user_id")
        batch_op.drop_column("review_requested_by_user_id")
        batch_op.drop_column("disputed_by_user_id")
