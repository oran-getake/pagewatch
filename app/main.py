from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, token_hash
from app.config import settings
from app.db import get_db
from app.models import Change, CheckJob, User, WatchTarget
from app.schemas import (
    AnonymousDeviceOut,
    ChangeDetailOut,
    ChangeSummaryOut,
    JobOut,
    MessageOut,
    WatchCreate,
    WatchOut,
    WatchUpdate,
)
from app.services.checker import next_check_time
from app.services.jobs import enqueue_job, find_active_job
from app.services.url_security import (
    UnsafeURLError,
    resolve_public_target,
)

app = FastAPI(
    title="PageWatch API",
    version="0.1.0",
    description="登録したWebページの文字変更を監視するAPI",
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def _owned_watch(session: Session, user: User, watch_id: str) -> WatchTarget:
    watch = session.scalar(
        select(WatchTarget).where(
            WatchTarget.id == watch_id, WatchTarget.user_id == user.id
        )
    )
    if watch is None:
        raise HTTPException(status_code=404, detail="監視ページが見つかりません。")
    return watch


@app.get("/health")
def health(session: Session = Depends(get_db)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post(
    "/api/devices/anonymous",
    response_model=AnonymousDeviceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_anonymous_device(session: Session = Depends(get_db)) -> AnonymousDeviceOut:
    token = secrets.token_urlsafe(32)
    session.add(User(device_token_hash=token_hash(token)))
    session.commit()
    return AnonymousDeviceOut(access_token=token)


@app.post(
    "/api/watches",
    response_model=WatchOut,
    status_code=status.HTTP_201_CREATED,
)
def create_watch(
    payload: WatchCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> WatchTarget:
    count = session.scalar(
        select(func.count())
        .select_from(WatchTarget)
        .where(WatchTarget.user_id == user.id)
    )
    if count >= 5:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="初版では1端末につき5件まで登録できます。",
        )

    try:
        # Resolve once at registration to reject invalid/internal destinations.
        normalized = resolve_public_target(payload.url).normalized_url
    except UnsafeURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    watch = WatchTarget(
        user_id=user.id,
        title=payload.title.strip(),
        url=normalized,
        url_hash=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        category=payload.category,
        frequency=payload.frequency,
        is_active=True,
        last_check_status="pending",
        next_check_at=utcnow(),
    )
    session.add(watch)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="同じURLはすでに登録されています。",
        ) from exc

    enqueue_job(session, watch, "initial", commit=False)
    session.commit()
    session.refresh(watch)
    return watch


@app.get("/api/watches", response_model=list[WatchOut])
def list_watches(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[WatchTarget]:
    return list(
        session.scalars(
            select(WatchTarget)
            .where(WatchTarget.user_id == user.id)
            .order_by(WatchTarget.created_at.desc())
        ).all()
    )


@app.get("/api/watches/{watch_id}", response_model=WatchOut)
def get_watch(
    watch_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> WatchTarget:
    return _owned_watch(session, user, watch_id)


@app.patch("/api/watches/{watch_id}", response_model=WatchOut)
def update_watch(
    watch_id: str,
    payload: WatchUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> WatchTarget:
    watch = _owned_watch(session, user, watch_id)
    changes = payload.model_dump(exclude_unset=True)

    if "title" in changes:
        watch.title = changes["title"].strip()
    if "category" in changes:
        watch.category = changes["category"]
    if "frequency" in changes:
        watch.frequency = changes["frequency"]
        watch.next_check_at = next_check_time(watch.frequency)
    if "is_active" in changes:
        watch.is_active = changes["is_active"]
        if watch.is_active:
            watch.last_check_status = "pending"
            watch.next_check_at = utcnow()
        else:
            watch.last_check_status = "paused"
            watch.next_check_at = None
            session.execute(
                update(CheckJob)
                .where(
                    CheckJob.watch_target_id == watch.id,
                    CheckJob.status == "queued",
                )
                .values(status="cancelled", finished_at=utcnow())
            )

    session.commit()
    if watch.is_active and "is_active" in changes:
        enqueue_job(session, watch, "resume")
    session.refresh(watch)
    return watch


@app.delete(
    "/api/watches/{watch_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_watch(
    watch_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    watch = _owned_watch(session, user, watch_id)
    session.delete(watch)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/watches/{watch_id}/check",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def manual_check(
    watch_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CheckJob:
    watch = _owned_watch(session, user, watch_id)
    if not watch.is_active:
        raise HTTPException(
            status_code=409,
            detail="監視を再開してから確認してください。",
        )

    existing = find_active_job(session, watch.id)
    if existing is not None:
        return existing

    if watch.last_checked_at is not None:
        checked = watch.last_checked_at
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=UTC)
        elapsed = (utcnow() - checked).total_seconds()
        if elapsed < settings.manual_check_cooldown_seconds:
            wait_seconds = int(settings.manual_check_cooldown_seconds - elapsed) + 1
            raise HTTPException(
                status_code=429,
                detail=f"次の確認まで約{wait_seconds}秒お待ちください。",
                headers={"Retry-After": str(wait_seconds)},
            )

    return enqueue_job(session, watch, "manual")


@app.get("/api/check-jobs/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CheckJob:
    job = session.scalar(
        select(CheckJob)
        .join(WatchTarget, WatchTarget.id == CheckJob.watch_target_id)
        .where(CheckJob.id == job_id, WatchTarget.user_id == user.id)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="確認処理が見つかりません。")
    return job


@app.get(
    "/api/watches/{watch_id}/changes",
    response_model=list[ChangeSummaryOut],
)
def list_changes(
    watch_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[Change]:
    watch = _owned_watch(session, user, watch_id)
    return list(
        session.scalars(
            select(Change)
            .where(Change.watch_target_id == watch.id)
            .order_by(Change.changed_at.desc())
            .limit(50)
        ).all()
    )


@app.get(
    "/api/watches/{watch_id}/changes/{change_id}",
    response_model=ChangeDetailOut,
)
def get_change(
    watch_id: str,
    change_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ChangeDetailOut:
    watch = _owned_watch(session, user, watch_id)
    change = session.scalar(
        select(Change).where(Change.id == change_id, Change.watch_target_id == watch.id)
    )
    if change is None:
        raise HTTPException(status_code=404, detail="変更履歴が見つかりません。")
    return ChangeDetailOut(
        id=change.id,
        added_text=change.added_text,
        removed_text=change.removed_text,
        diff_truncated=change.diff_truncated,
        changed_at=change.changed_at,
        before_text=change.previous_snapshot.content_text,
        after_text=change.current_snapshot.content_text,
        source_url=watch.url,
    )


@app.get("/api/account/usage", response_model=dict[str, int])
def account_usage(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict[str, int]:
    count = session.scalar(
        select(func.count())
        .select_from(WatchTarget)
        .where(WatchTarget.user_id == user.id)
    )
    return {"registered": int(count or 0), "limit": 5}


@app.delete(
    "/api/account",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_account(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    session.delete(user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", response_model=MessageOut)
def root() -> MessageOut:
    return MessageOut(message="PageWatch API")
