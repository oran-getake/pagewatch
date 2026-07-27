from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from app.services.fetcher import USER_AGENT, FetchError, safe_fetch


@dataclass(frozen=True)
class _CacheEntry:
    allowed_parser: RobotFileParser | None
    force_allowed: bool | None
    expires_at: float


_cache: dict[str, _CacheEntry] = {}
_lock = threading.Lock()
CACHE_SECONDS = 6 * 60 * 60


def _origin_and_robots_url(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
    robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
    return origin, robots_url


def is_allowed(url: str) -> bool:
    origin, robots_url = _origin_and_robots_url(url)
    now = time.monotonic()
    with _lock:
        cached = _cache.get(origin)
        if cached is not None and cached.expires_at > now:
            if cached.force_allowed is not None:
                return cached.force_allowed
            assert cached.allowed_parser is not None
            return cached.allowed_parser.can_fetch(USER_AGENT, url)

    parser: RobotFileParser | None = None
    force_allowed: bool | None
    try:
        response = safe_fetch(robots_url, max_bytes=128 * 1024)
        if response.status_code in {401, 403}:
            force_allowed = False
        elif response.status_code == 404:
            force_allowed = True
        elif 200 <= response.status_code < 300:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.body.splitlines())
            force_allowed = None
        else:
            force_allowed = True
    except FetchError:
        # A temporary robots.txt failure must not be cached for six hours.
        return True

    entry = _CacheEntry(
        allowed_parser=parser,
        force_allowed=force_allowed,
        expires_at=now + CACHE_SECONDS,
    )
    with _lock:
        _cache[origin] = entry

    if force_allowed is not None:
        return force_allowed
    assert parser is not None
    return parser.can_fetch(USER_AGENT, url)
