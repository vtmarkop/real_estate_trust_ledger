"""Add application-time score snapshot fields

Revision ID: 20260411_0015
Revises: 20260411_0014
Create Date: 2026-04-11 05:40:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0015"
down_revision: Union[str, Sequence[str], None] = "20260411_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listing_applications",
        sa.Column("applicant_tenant_score", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listing_applications",
        sa.Column("applicant_verification_strength", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listing_applications",
        sa.Column("applicant_score_version", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "listing_applications",
        sa.Column("applicant_score_calculated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("listing_applications", "applicant_score_calculated_at")
    op.drop_column("listing_applications", "applicant_score_version")
    op.drop_column("listing_applications", "applicant_verification_strength")
    op.drop_column("listing_applications", "applicant_tenant_score")
