from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CheckJob, WatchTarget
from app.services.checker import check_watch

ACTIVE_JOB_STATUSES = {"queued", "running"}


def utcnow() -> datetime:
    return datetime.now(UTC)


def find_active_job(session: Session, watch_id: str) -> CheckJob | None:
    return session.scalar(
        select(CheckJob)
        .where(
            CheckJob.watch_target_id == watch_id,
            CheckJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(CheckJob.created_at.asc())
        .limit(1)
    )


def enqueue_job(
    session: Session,
    watch: WatchTarget,
    source: str,
    *,
    commit: bool = True,
) -> CheckJob:
    existing = find_active_job(session, watch.id)
    if existing is not None:
        return existing

    job = CheckJob(
        watch_target_id=watch.id,
        source=source,
        status="queued",
        run_after=utcnow(),
    )
    session.add(job)
    try:
        if commit:
            session.commit()
            session.refresh(job)
        else:
            session.flush()
    except IntegrityError:
        session.rollback()
        existing = find_active_job(session, watch.id)
        if existing is None:
            raise
        return existing
    return job


def enqueue_due_jobs(session: Session) -> int:
    recover_stale_jobs(session)
    now = utcnow()
    watches = session.scalars(
        select(WatchTarget).where(
            WatchTarget.is_active.is_(True),
            WatchTarget.next_check_at.is_not(None),
            WatchTarget.next_check_at <= now,
        )
    ).all()

    count = 0
    for watch in watches:
        if find_active_job(session, watch.id) is None:
            enqueue_job(session, watch, "scheduled", commit=False)
            count += 1
    session.commit()
    return count


def recover_stale_jobs(session: Session) -> int:
    cutoff = utcnow() - timedelta(seconds=settings.stale_job_seconds)
    jobs = session.scalars(
        select(CheckJob).where(
            CheckJob.status == "running",
            CheckJob.started_at.is_not(None),
            CheckJob.started_at < cutoff,
        )
    ).all()
    now = utcnow()
    for job in jobs:
        if job.attempts >= settings.worker_max_attempts:
            job.status = "failed"
            job.finished_at = now
            job.error_message = "Worker停止により確認を完了できませんでした。"
        else:
            job.status = "queued"
            job.run_after = now
            job.started_at = None
            job.error_message = "Worker停止後に確認処理を再開しました。"
    session.commit()
    return len(jobs)


def claim_next_job(session: Session) -> CheckJob | None:
    now = utcnow()
    statement = (
        select(CheckJob)
        .where(CheckJob.status == "queued", CheckJob.run_after <= now)
        .order_by(CheckJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    job = session.scalar(statement)
    if job is None:
        return None
    job.status = "running"
    job.started_at = now
    job.attempts += 1
    session.commit()
    session.refresh(job)
    return job


def process_job(session: Session, job: CheckJob) -> None:
    watch = session.get(WatchTarget, job.watch_target_id)
    if watch is None or not watch.is_active:
        job.status = "cancelled"
        job.finished_at = utcnow()
        session.commit()
        return

    try:
        result = check_watch(session, watch, job.source)
        job.status = "succeeded" if result != "error" else "failed"
        job.error_message = watch.last_error
        job.finished_at = utcnow()
        session.commit()
    except Exception as exc:
        session.rollback()
        job = session.get(CheckJob, job.id)
        if job is None:
            raise
        if job.attempts < settings.worker_max_attempts:
            job.status = "queued"
            job.run_after = utcnow() + timedelta(seconds=30 * job.attempts)
            job.error_message = str(exc)[:500]
        else:
            job.status = "failed"
            job.finished_at = utcnow()
            job.error_message = str(exc)[:500]
        session.commit()
