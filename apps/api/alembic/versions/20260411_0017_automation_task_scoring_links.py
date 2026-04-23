"""Link automation tasks to queued score recalculation records

Revision ID: 20260411_0017
Revises: 20260411_0016
Create Date: 2026-04-11 08:05:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0017"
down_revision: Union[str, Sequence[str], None] = "20260411_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("automation_tasks", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("score_recalculation_request_id", sa.Uuid(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("score_recalculation_batch_id", sa.Uuid(), nullable=True),
        )
        batch_op.create_index(
            batch_op.f("ix_automation_tasks_score_recalculation_request_id"),
            ["score_recalculation_request_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_automation_tasks_score_recalculation_batch_id"),
            ["score_recalculation_batch_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_automation_tasks_score_recalculation_request_id",
            "trust_score_recalculation_requests",
            ["score_recalculation_request_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_automation_tasks_score_recalculation_batch_id",
            "trust_score_recalculation_batches",
            ["score_recalculation_batch_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("automation_tasks", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_automation_tasks_score_recalculation_batch_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_automation_tasks_score_recalculation_request_id",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_automation_tasks_score_recalculation_batch_id"))
        batch_op.drop_index(batch_op.f("ix_automation_tasks_score_recalculation_request_id"))
        batch_op.drop_column("score_recalculation_batch_id")
        batch_op.drop_column("score_recalculation_request_id")
