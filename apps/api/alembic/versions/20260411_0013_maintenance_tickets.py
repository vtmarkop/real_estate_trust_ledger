"""Add maintenance tickets and trust-event maintenance linkage

Revision ID: 20260411_0013
Revises: 20260411_0012
Create Date: 2026-04-11 04:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0013"
down_revision: Union[str, Sequence[str], None] = "20260411_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "maintenance_tickets",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenancy_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("acknowledged_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("resolved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("disputed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("ticket_status", sa.String(length=32), nullable=False),
        sa.Column("reported_artifact_name", sa.String(length=255), nullable=True),
        sa.Column("landlord_response_notes", sa.String(length=1000), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_summary", sa.String(length=1000), nullable=True),
        sa.Column("resolution_artifact_name", sa.String(length=255), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispute_notes", sa.String(length=1000), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["acknowledged_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["disputed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_tickets_tenancy_id",
        "maintenance_tickets",
        ["tenancy_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_tickets_created_by_user_id",
        "maintenance_tickets",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_tickets_acknowledged_by_user_id",
        "maintenance_tickets",
        ["acknowledged_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_tickets_resolved_by_user_id",
        "maintenance_tickets",
        ["resolved_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_tickets_disputed_by_user_id",
        "maintenance_tickets",
        ["disputed_by_user_id"],
        unique=False,
    )

    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("maintenance_ticket_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trust_events_maintenance_ticket_id",
            "maintenance_tickets",
            ["maintenance_ticket_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_events_maintenance_ticket_id",
            ["maintenance_ticket_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("trust_events", recreate="auto") as batch_op:
        batch_op.drop_index("ix_trust_events_maintenance_ticket_id")
        batch_op.drop_constraint("fk_trust_events_maintenance_ticket_id", type_="foreignkey")
        batch_op.drop_column("maintenance_ticket_id")

    op.drop_index(
        "ix_maintenance_tickets_disputed_by_user_id",
        table_name="maintenance_tickets",
    )
    op.drop_index(
        "ix_maintenance_tickets_resolved_by_user_id",
        table_name="maintenance_tickets",
    )
    op.drop_index(
        "ix_maintenance_tickets_acknowledged_by_user_id",
        table_name="maintenance_tickets",
    )
    op.drop_index(
        "ix_maintenance_tickets_created_by_user_id",
        table_name="maintenance_tickets",
    )
    op.drop_index("ix_maintenance_tickets_tenancy_id", table_name="maintenance_tickets")
    op.drop_table("maintenance_tickets")
