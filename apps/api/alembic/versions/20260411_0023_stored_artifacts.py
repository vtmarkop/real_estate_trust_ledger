"""Add stored artifacts and evidence artifact linkage

Revision ID: 20260411_0023
Revises: 20260411_0022
Create Date: 2026-04-11 21:15:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260411_0023"
down_revision: Union[str, Sequence[str], None] = "20260411_0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "stored_artifacts" not in inspector.get_table_names():
        op.create_table(
            "stored_artifacts",
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
            sa.Column("tenancy_id", sa.Uuid(), nullable=False),
            sa.Column("artifact_purpose", sa.String(length=64), nullable=False),
            sa.Column("storage_backend", sa.String(length=32), nullable=False),
            sa.Column("storage_key", sa.String(length=500), nullable=False),
            sa.Column("original_file_name", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=255), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256_hex", sa.String(length=64), nullable=False),
            sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["tenancy_id"], ["tenancies.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)
    stored_artifact_indexes = {
        index["name"] for index in inspector.get_indexes("stored_artifacts")
    }
    if "ix_stored_artifacts_created_by_user_id" not in stored_artifact_indexes:
        op.create_index(
            "ix_stored_artifacts_created_by_user_id",
            "stored_artifacts",
            ["created_by_user_id"],
            unique=False,
        )
    if "ix_stored_artifacts_tenancy_id" not in stored_artifact_indexes:
        op.create_index(
            "ix_stored_artifacts_tenancy_id",
            "stored_artifacts",
            ["tenancy_id"],
            unique=False,
        )
    if "ix_stored_artifacts_storage_key" not in stored_artifact_indexes:
        op.create_index(
            "ix_stored_artifacts_storage_key",
            "stored_artifacts",
            ["storage_key"],
            unique=True,
        )

    evidence_columns = {
        column["name"] for column in inspector.get_columns("evidence_documents")
    }
    if "stored_artifact_id" not in evidence_columns:
        with op.batch_alter_table("evidence_documents") as batch_op:
            batch_op.add_column(sa.Column("stored_artifact_id", sa.Uuid(), nullable=True))

    inspector = sa.inspect(bind)
    evidence_indexes = {
        index["name"] for index in inspector.get_indexes("evidence_documents")
    }
    evidence_foreign_keys = {
        foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("evidence_documents")
    }
    with op.batch_alter_table("evidence_documents") as batch_op:
        if "ix_evidence_documents_stored_artifact_id" not in evidence_indexes:
            batch_op.create_index(
                "ix_evidence_documents_stored_artifact_id",
                ["stored_artifact_id"],
                unique=False,
            )
        if "fk_evidence_documents_stored_artifact_id" not in evidence_foreign_keys:
            batch_op.create_foreign_key(
                "fk_evidence_documents_stored_artifact_id",
                "stored_artifacts",
                ["stored_artifact_id"],
                ["id"],
            )


def downgrade() -> None:
    with op.batch_alter_table("evidence_documents") as batch_op:
        batch_op.drop_constraint(
            "fk_evidence_documents_stored_artifact_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_evidence_documents_stored_artifact_id")
        batch_op.drop_column("stored_artifact_id")

    op.drop_index("ix_stored_artifacts_storage_key", table_name="stored_artifacts")
    op.drop_index("ix_stored_artifacts_tenancy_id", table_name="stored_artifacts")
    op.drop_index("ix_stored_artifacts_created_by_user_id", table_name="stored_artifacts")
    op.drop_table("stored_artifacts")
