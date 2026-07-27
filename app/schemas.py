from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["job", "product", "real_estate", "ticket", "notice", "other"]
Frequency = Literal["daily", "three_daily", "six_daily"]


class AnonymousDeviceOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WatchCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=8, max_length=2048)
    category: Category = "other"
    frequency: Frequency = "daily"


class WatchUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    category: Category | None = None
    frequency: Frequency | None = None
    is_active: bool | None = None


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    url: str
    category: str
    frequency: str
    is_active: bool
    last_check_status: str
    last_error: str | None
    last_checked_at: datetime | None
    next_check_at: datetime | None
    created_at: datetime
    updated_at: datetime


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    watch_target_id: str
    source: str
    status: str
    attempts: int
    run_after: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime


class ChangeSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    added_text: str
    removed_text: str
    diff_truncated: bool
    changed_at: datetime


class ChangeDetailOut(ChangeSummaryOut):
    before_text: str
    after_text: str
    source_url: str


class MessageOut(BaseModel):
    message: str
