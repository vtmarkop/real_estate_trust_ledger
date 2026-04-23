"""Add agency trust check audit table

Revision ID: 20260409_0002
Revises: 20260409_0001
Create Date: 2026-04-09 00:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0002"
down_revision: Union[str, Sequence[str], None] = "20260409_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


consent_scope_enum = sa.Enum(
    "trust_report:read",
    "trust_check:run",
    name="consentscope",
)


def upgrade() -> None:
    op.create_table(
        "agency_trust_checks",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("consent_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("subject_user_id", sa.Uuid(), nullable=False),
        sa.Column("scope", consent_scope_enum, nullable=False),
        sa.ForeignKeyConstraint(["consent_id"], ["trust_report_consents.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agency_trust_checks_organization_id",
        "agency_trust_checks",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_agency_trust_checks_consent_id",
        "agency_trust_checks",
        ["consent_id"],
        unique=False,
    )
    op.create_index(
        "ix_agency_trust_checks_subject_user_id",
        "agency_trust_checks",
        ["subject_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agency_trust_checks_subject_user_id", table_name="agency_trust_checks")
    op.drop_index("ix_agency_trust_checks_consent_id", table_name="agency_trust_checks")
    op.drop_index("ix_agency_trust_checks_organization_id", table_name="agency_trust_checks")
    op.drop_table("agency_trust_checks")
