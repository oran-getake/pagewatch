from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    device_token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    watches: Mapped[list[WatchTarget]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class WatchTarget(Base):
    __tablename__ = "watch_targets"
    __table_args__ = (
        UniqueConstraint("user_id", "url_hash", name="uq_watch_user_url"),
        Index("ix_watch_due", "is_active", "next_check_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    frequency: Mapped[str] = mapped_column(String(24), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_check_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="pending"
    )
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    user: Mapped[User] = relationship(back_populates="watches")
    snapshots: Mapped[list[Snapshot]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )
    changes: Mapped[list[Change]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )
    logs: Mapped[list[CheckLog]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )
    jobs: Mapped[list[CheckJob]] = relationship(
        back_populates="watch", cascade="all, delete-orphan"
    )


class Snapshot(Base):
    __tablename__ = "snapshots"
    __table_args__ = (
        Index("ix_snapshot_watch_checked", "watch_target_id", "checked_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    watch_target_id: Mapped[str] = mapped_column(
        ForeignKey("watch_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    http_status: Mapped[int] = mapped_column(Integer, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    watch: Mapped[WatchTarget] = relationship(back_populates="snapshots")


class Change(Base):
    __tablename__ = "changes"
    __table_args__ = (
        Index("ix_change_watch_changed", "watch_target_id", "changed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    watch_target_id: Mapped[str] = mapped_column(
        ForeignKey("watch_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    current_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    added_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    removed_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    diff_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    watch: Mapped[WatchTarget] = relationship(back_populates="changes")
    previous_snapshot: Mapped[Snapshot] = relationship(
        foreign_keys=[previous_snapshot_id]
    )
    current_snapshot: Mapped[Snapshot] = relationship(
        foreign_keys=[current_snapshot_id]
    )


class CheckLog(Base):
    __tablename__ = "check_logs"
    __table_args__ = (Index("ix_log_watch_checked", "watch_target_id", "checked_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    watch_target_id: Mapped[str] = mapped_column(
        ForeignKey("watch_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    watch: Mapped[WatchTarget] = relationship(back_populates="logs")


class CheckJob(Base):
    __tablename__ = "check_jobs"
    __table_args__ = (
        Index("ix_job_claim", "status", "run_after", "created_at"),
        Index(
            "uq_active_job_per_watch",
            "watch_target_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
            sqlite_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    watch_target_id: Mapped[str] = mapped_column(
        ForeignKey("watch_targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    watch: Mapped[WatchTarget] = relationship(back_populates="jobs")
