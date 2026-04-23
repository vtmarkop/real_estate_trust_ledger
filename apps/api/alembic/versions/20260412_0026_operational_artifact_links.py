"""add operational artifact links

Revision ID: 20260412_0026
Revises: 20260412_0025
Create Date: 2026-04-12 18:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0026"
down_revision = "20260412_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment_records", schema=None) as batch_op:
        batch_op.add_column(sa.Column("proof_stored_artifact_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_payment_records_proof_stored_artifact_id",
            ["proof_stored_artifact_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_payment_records_proof_stored_artifact_id_stored_artifacts",
            "stored_artifacts",
            ["proof_stored_artifact_id"],
            ["id"],
        )

    with op.batch_alter_table("deposit_records", schema=None) as batch_op:
        batch_op.add_column(sa.Column("settlement_stored_artifact_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_deposit_records_settlement_stored_artifact_id",
            ["settlement_stored_artifact_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_deposit_records_settlement_stored_artifact_id_stored_artifacts",
            "stored_artifacts",
            ["settlement_stored_artifact_id"],
            ["id"],
        )

    with op.batch_alter_table("maintenance_tickets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("reported_stored_artifact_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("resolution_stored_artifact_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            "ix_maintenance_tickets_reported_stored_artifact_id",
            ["reported_stored_artifact_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_maintenance_tickets_resolution_stored_artifact_id",
            ["resolution_stored_artifact_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_maintenance_tickets_reported_stored_artifact_id_stored_artifacts",
            "stored_artifacts",
            ["reported_stored_artifact_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_maintenance_tickets_resolution_stored_artifact_id_stored_artifacts",
            "stored_artifacts",
            ["resolution_stored_artifact_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("maintenance_tickets", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_maintenance_tickets_resolution_stored_artifact_id_stored_artifacts",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_maintenance_tickets_reported_stored_artifact_id_stored_artifacts",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_maintenance_tickets_resolution_stored_artifact_id")
        batch_op.drop_index("ix_maintenance_tickets_reported_stored_artifact_id")
        batch_op.drop_column("resolution_stored_artifact_id")
        batch_op.drop_column("reported_stored_artifact_id")

    with op.batch_alter_table("deposit_records", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_deposit_records_settlement_stored_artifact_id_stored_artifacts",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_deposit_records_settlement_stored_artifact_id")
        batch_op.drop_column("settlement_stored_artifact_id")

    with op.batch_alter_table("payment_records", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_payment_records_proof_stored_artifact_id_stored_artifacts",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_payment_records_proof_stored_artifact_id")
        batch_op.drop_column("proof_stored_artifact_id")
