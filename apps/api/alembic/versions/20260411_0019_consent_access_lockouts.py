"""Add consent access attempt tracking and lockouts

Revision ID: 20260411_0019
Revises: 20260411_0018
Create Date: 2026-04-11 10:05:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0019"
down_revision: Union[str, Sequence[str], None] = "20260411_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trust_report_consents",
        sa.Column(
            "failed_access_attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "trust_report_consents",
        sa.Column("last_access_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "trust_report_consents",
        sa.Column("access_locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "trust_report_consents",
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trust_report_consents", "last_validated_at")
    op.drop_column("trust_report_consents", "access_locked_until")
    op.drop_column("trust_report_consents", "last_access_attempt_at")
    op.drop_column("trust_report_consents", "failed_access_attempt_count")
