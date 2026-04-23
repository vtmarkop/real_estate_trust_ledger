"""Add score recalculation request processing tracking

Revision ID: 20260411_0021
Revises: 20260411_0020
Create Date: 2026-04-11 18:10:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0021"
down_revision: Union[str, Sequence[str], None] = "20260411_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_score_recalculation_requests",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.add_column(sa.Column("processed_by_user_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "attempt_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.create_foreign_key(
            "fk_trust_score_recalculation_requests_processed_by_user_id_users",
            "users",
            ["processed_by_user_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_trust_score_recalculation_requests_processed_by_user_id",
            ["processed_by_user_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table(
        "trust_score_recalculation_requests",
        recreate="always" if bind.dialect.name == "sqlite" else "auto",
    ) as batch_op:
        batch_op.drop_index("ix_trust_score_recalculation_requests_processed_by_user_id")
        batch_op.drop_constraint(
            "fk_trust_score_recalculation_requests_processed_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("attempt_count")
        batch_op.drop_column("processed_by_user_id")
