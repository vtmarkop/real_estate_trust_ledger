"""Add score-aware listing threshold columns

Revision ID: 20260411_0014
Revises: 20260411_0013
Create Date: 2026-04-11 05:05:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0014"
down_revision: Union[str, Sequence[str], None] = "20260411_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("minimum_tenant_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "listings",
        sa.Column("minimum_verification_strength", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("listings", "minimum_verification_strength")
    op.drop_column("listings", "minimum_tenant_score")
