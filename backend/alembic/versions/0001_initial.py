"""Initial schema for DecisionAI.

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("stored_path", sa.String(1000), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("row_count", sa.Integer, server_default="0"),
        sa.Column("column_count", sa.Integer, server_default="0"),
        sa.Column("file_size_bytes", sa.Integer, server_default="0"),
        sa.Column("preview", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_datasets_user_id", "datasets", ["user_id"])

    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column("summary", postgresql.JSON, server_default="{}"),
        sa.Column("kpis", postgresql.JSON, server_default="{}"),
        sa.Column("quality_score", sa.Float, server_default="0"),
        sa.Column("health_score", sa.Float, server_default="0"),
        sa.Column("diagnosis", postgresql.JSON, server_default="{}"),
        sa.Column("root_causes", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analyses_dataset_id", "analyses", ["dataset_id"])
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=True),
        sa.Column("best_model", sa.String(255), nullable=True),
        sa.Column("metrics", postgresql.JSON, server_default="{}"),
        sa.Column("feature_importance", postgresql.JSON, server_default="{}"),
        sa.Column("predictions", postgresql.JSON, server_default="{}"),
        sa.Column("model_artifact_path", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_predictions_dataset_id", "predictions", ["dataset_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendations", postgresql.JSON, server_default="{}"),
        sa.Column("executive_summary", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("download_url", sa.String(1000), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chat_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("context", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_history_dataset_id", "chat_history", ["dataset_id"])

    op.create_table(
        "uploaded_files",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("stored_name", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource", sa.String(255), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("details", postgresql.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("uploaded_files")
    op.drop_table("chat_history")
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("predictions")
    op.drop_table("analyses")
    op.drop_table("datasets")
    op.drop_table("users")
