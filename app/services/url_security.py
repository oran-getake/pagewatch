from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


class UnsafeURLError(ValueError):
    pass


BLOCKED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".home.arpa",
)


@dataclass(frozen=True)
class ResolvedTarget:
    normalized_url: str
    scheme: str
    hostname: str
    port: int
    addresses: tuple[str, ...]


def normalize_url(url: str) -> str:
    raw = url.strip()
    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError as exc:
        raise UnsafeURLError("URLの形式が正しくありません。") from exc

    if parts.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError("http または https のURLだけ登録できます。")
    if not parts.hostname:
        raise UnsafeURLError("URLにホスト名がありません。")
    if parts.username or parts.password:
        raise UnsafeURLError("認証情報を含むURLは登録できません。")

    scheme = parts.scheme.lower()
    expected_port = 443 if scheme == "https" else 80
    if port is not None and port != expected_port:
        raise UnsafeURLError("初版では標準ポートのURLだけ登録できます。")

    try:
        hostname = parts.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError as exc:
        raise UnsafeURLError("ホスト名を解釈できません。") from exc

    if hostname == "localhost" or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise UnsafeURLError("ローカルネットワークのURLは登録できません。")

    netloc = hostname
    try:
        if isinstance(ipaddress.ip_address(hostname), ipaddress.IPv6Address):
            netloc = f"[{hostname}]"
    except ValueError:
        pass

    path = parts.path or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global


def resolve_public_target(url: str) -> ResolvedTarget:
    normalized = normalize_url(url)
    parts = urlsplit(normalized)
    assert parts.hostname is not None
    port = parts.port or (443 if parts.scheme == "https" else 80)

    try:
        info = socket.getaddrinfo(
            parts.hostname,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise UnsafeURLError("URLのホスト名を確認できません。") from exc

    addresses = tuple(dict.fromkeys(item[4][0] for item in info))
    if not addresses:
        raise UnsafeURLError("URLの接続先が見つかりません。")
    if any(not is_public_ip(address) for address in addresses):
        raise UnsafeURLError("内部ネットワークにつながるURLは登録できません。")

    return ResolvedTarget(
        normalized_url=normalized,
        scheme=parts.scheme,
        hostname=parts.hostname,
        port=port,
        addresses=addresses,
    )
