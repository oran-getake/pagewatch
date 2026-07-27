from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Change, CheckLog, Snapshot, WatchTarget
from app.services.differ import compare_text
from app.services.extractor import ExtractionError, extract_visible_text
from app.services.fetcher import FetchError, safe_fetch
from app.services.robots import is_allowed

FREQUENCY_INTERVALS = {
    "daily": timedelta(days=1),
    "three_daily": timedelta(hours=8),
    "six_daily": timedelta(hours=4),
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def next_check_time(frequency: str, base: datetime | None = None) -> datetime:
    return (base or utcnow()) + FREQUENCY_INTERVALS.get(frequency, timedelta(days=1))


def _latest_snapshot(session: Session, watch_id: str) -> Snapshot | None:
    return session.scalar(
        select(Snapshot)
        .where(Snapshot.watch_target_id == watch_id)
        .order_by(Snapshot.checked_at.desc())
        .limit(1)
    )


def _record_error(
    session: Session,
    watch: WatchTarget,
    source: str,
    message: str,
    *,
    http_status: int | None = None,
) -> None:
    now = utcnow()
    watch.last_check_status = "error"
    watch.last_error = message[:500]
    watch.last_checked_at = now
    watch.next_check_at = next_check_time(watch.frequency, now)
    session.add(
        CheckLog(
            watch_target_id=watch.id,
            source=source,
            status="error",
            http_status=http_status,
            error_message=message[:500],
            checked_at=now,
        )
    )


def check_watch(session: Session, watch: WatchTarget, source: str) -> str:
    if not watch.is_active:
        raise RuntimeError("停止中のページは確認できません。")

    try:
        if not is_allowed(watch.url):
            raise FetchError("対象サイトのrobots.txtにより自動確認が禁止されています。")

        response = safe_fetch(watch.url)
        if response.status_code == 404:
            raise FetchError("ページが削除された可能性があります。")
        if response.status_code in {401, 403}:
            raise FetchError("対象サイトからアクセスを拒否されました。")
        if response.status_code == 429:
            raise FetchError("対象サイトのアクセス上限に達しました。")
        if response.status_code >= 400:
            raise FetchError(
                f"ページ取得に失敗しました（HTTP {response.status_code}）。"
            )

        content_text = extract_visible_text(response.body)
    except (FetchError, ExtractionError) as exc:
        http_status = response.status_code if "response" in locals() else None
        _record_error(
            session,
            watch,
            source,
            str(exc),
            http_status=http_status,
        )
        return "error"

    now = utcnow()
    content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
    previous = _latest_snapshot(session, watch.id)
    result_status = "unchanged"

    if previous is None:
        session.add(
            Snapshot(
                watch_target_id=watch.id,
                content_text=content_text,
                content_hash=content_hash,
                http_status=response.status_code,
                checked_at=now,
            )
        )
    elif previous.content_hash != content_hash:
        current = Snapshot(
            watch_target_id=watch.id,
            content_text=content_text,
            content_hash=content_hash,
            http_status=response.status_code,
            checked_at=now,
        )
        session.add(current)
        session.flush()
        diff = compare_text(previous.content_text, current.content_text)
        session.add(
            Change(
                watch_target_id=watch.id,
                previous_snapshot_id=previous.id,
                current_snapshot_id=current.id,
                added_text=diff.added_text,
                removed_text=diff.removed_text,
                diff_truncated=diff.truncated,
                changed_at=now,
            )
        )
        result_status = "changed"

    watch.last_check_status = result_status
    watch.last_error = None
    watch.last_checked_at = now
    watch.next_check_at = next_check_time(watch.frequency, now)
    session.add(
        CheckLog(
            watch_target_id=watch.id,
            source=source,
            status=result_status,
            http_status=response.status_code,
            checked_at=now,
        )
    )
    return result_status
