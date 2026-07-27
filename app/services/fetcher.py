from __future__ import annotations

import http.client
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from app.config import settings
from app.services.url_security import UnsafeURLError, resolve_public_target

USER_AGENT = "PageWatchBot/0.1 (+https://example.invalid/pagewatch)"
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class FetchError(RuntimeError):
    pass


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        address: str,
        *,
        port: int,
        server_hostname: str,
        timeout: int,
    ) -> None:
        super().__init__(
            address,
            port=port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self._pagewatch_server_hostname = server_hostname

    def connect(self) -> None:
        http.client.HTTPConnection.connect(self)
        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=self._pagewatch_server_hostname,
        )


@dataclass(frozen=True)
class FetchResponse:
    final_url: str
    status_code: int
    content_type: str
    body: str


def _decode_body(data: bytes, content_type: str) -> str:
    charset = ""
    for part in content_type.split(";")[1:]:
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset":
            charset = value.strip("\"'")
            break
    candidates = [charset, "utf-8", "cp932", "shift_jis"]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return data.decode(candidate)
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", errors="replace")


def _host_header(hostname: str, scheme: str, port: int) -> str:
    host = f"[{hostname}]" if ":" in hostname else hostname
    expected = 443 if scheme == "https" else 80
    return host if port == expected else f"{host}:{port}"


def _request_once(url: str, max_bytes: int) -> tuple[int, dict[str, str], bytes]:
    target = resolve_public_target(url)
    parts = urlsplit(target.normalized_url)
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"

    last_error: Exception | None = None
    for address in target.addresses:
        connection: http.client.HTTPConnection
        if target.scheme == "https":
            connection = _PinnedHTTPSConnection(
                address,
                port=target.port,
                server_hostname=target.hostname,
                timeout=settings.fetch_timeout_seconds,
            )
        else:
            connection = http.client.HTTPConnection(
                address,
                port=target.port,
                timeout=settings.fetch_timeout_seconds,
            )

        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Host": _host_header(target.hostname, target.scheme, target.port),
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            headers = {key.lower(): value for key, value in response.getheaders()}
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise FetchError("ページのデータ量が上限を超えています。")
            return response.status, headers, body
        except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
        finally:
            connection.close()

    raise FetchError("ページへ接続できませんでした。") from last_error


def safe_fetch(
    url: str,
    *,
    max_bytes: int | None = None,
    max_redirects: int = 3,
) -> FetchResponse:
    limit = max_bytes or settings.max_response_bytes
    current = url
    for redirect_count in range(max_redirects + 1):
        try:
            normalized = resolve_public_target(current).normalized_url
        except UnsafeURLError as exc:
            raise FetchError(str(exc)) from exc

        status, headers, raw = _request_once(normalized, limit)
        if status in REDIRECT_STATUSES:
            location = headers.get("location")
            if not location:
                raise FetchError("転送先のないリダイレクトが返されました。")
            if redirect_count >= max_redirects:
                raise FetchError("ページの転送回数が上限を超えています。")
            current = urljoin(normalized, location)
            continue

        content_type = headers.get("content-type", "").lower()
        media_type = content_type.split(";", 1)[0].strip()
        if status < 400 and not any(
            media_type.startswith(allowed) for allowed in ALLOWED_CONTENT_TYPES
        ):
            raise FetchError("文字ページではないため監視できません。")

        return FetchResponse(
            final_url=normalized,
            status_code=status,
            content_type=content_type,
            body=_decode_body(raw, content_type),
        )

    raise FetchError("ページの転送を完了できませんでした。")
