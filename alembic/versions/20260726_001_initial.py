"""Initial PageWatch schema.

Revision ID: 20260726_001
Revises:
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260726_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("device_token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_users_device_token_hash",
        "users",
        ["device_token_hash"],
        unique=True,
    )

    op.create_table(
        "watch_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("frequency", sa.String(length=24), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_check_status", sa.String(length=24), nullable=False),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "url_hash", name="uq_watch_user_url"),
    )
    op.create_index("ix_watch_targets_user_id", "watch_targets", ["user_id"])
    op.create_index("ix_watch_due", "watch_targets", ["is_active", "next_check_at"])

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("watch_target_id", sa.String(length=36), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["watch_target_id"], ["watch_targets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshots_watch_target_id", "snapshots", ["watch_target_id"])
    op.create_index(
        "ix_snapshot_watch_checked",
        "snapshots",
        ["watch_target_id", "checked_at"],
    )

    op.create_table(
        "changes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("watch_target_id", sa.String(length=36), nullable=False),
        sa.Column("previous_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("current_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("added_text", sa.Text(), nullable=False),
        sa.Column("removed_text", sa.Text(), nullable=False),
        sa.Column("diff_truncated", sa.Boolean(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["current_snapshot_id"], ["snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["previous_snapshot_id"], ["snapshots.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["watch_target_id"], ["watch_targets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_changes_watch_target_id", "changes", ["watch_target_id"])
    op.create_index(
        "ix_change_watch_changed", "changes", ["watch_target_id", "changed_at"]
    )

    op.create_table(
        "check_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("watch_target_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["watch_target_id"], ["watch_targets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_check_logs_watch_target_id", "check_logs", ["watch_target_id"])
    op.create_index(
        "ix_log_watch_checked", "check_logs", ["watch_target_id", "checked_at"]
    )

    op.create_table(
        "check_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("watch_target_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["watch_target_id"], ["watch_targets.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_check_jobs_watch_target_id", "check_jobs", ["watch_target_id"])
    op.create_index("ix_job_claim", "check_jobs", ["status", "run_after", "created_at"])
    op.create_index(
        "uq_active_job_per_watch",
        "check_jobs",
        ["watch_target_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
        sqlite_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_table("check_jobs")
    op.drop_table("check_logs")
    op.drop_table("changes")
    op.drop_table("snapshots")
    op.drop_table("watch_targets")
    op.drop_table("users")
