from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str
    environment: str
    device_token_pepper: str
    fetch_timeout_seconds: int
    max_response_bytes: int
    max_extracted_chars: int
    manual_check_cooldown_seconds: int
    worker_poll_seconds: int
    worker_max_attempts: int
    stale_job_seconds: int

    @classmethod
    def from_env(cls) -> Settings:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./pagewatch.db")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        environment = os.getenv("ENVIRONMENT", "development")
        pepper = os.getenv("DEVICE_TOKEN_PEPPER", "")
        if environment == "production" and len(pepper) < 32:
            raise RuntimeError(
                "DEVICE_TOKEN_PEPPER must be at least 32 characters in production"
            )

        return cls(
            database_url=database_url,
            environment=environment,
            device_token_pepper=pepper,
            fetch_timeout_seconds=_int_env("FETCH_TIMEOUT_SECONDS", 15),
            max_response_bytes=_int_env("MAX_RESPONSE_BYTES", 2 * 1024 * 1024),
            max_extracted_chars=_int_env("MAX_EXTRACTED_CHARS", 300_000),
            manual_check_cooldown_seconds=_int_env(
                "MANUAL_CHECK_COOLDOWN_SECONDS", 300
            ),
            worker_poll_seconds=_int_env("WORKER_POLL_SECONDS", 2),
            worker_max_attempts=_int_env("WORKER_MAX_ATTEMPTS", 3),
            stale_job_seconds=_int_env("STALE_JOB_SECONDS", 600),
        )


settings = Settings.from_env()
