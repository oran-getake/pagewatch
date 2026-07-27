from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class TextDiff:
    added_text: str
    removed_text: str
    truncated: bool


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    suffix = "\n…差分が長いため省略しました。"
    return value[: max(0, limit - len(suffix))] + suffix, True


def compare_text(before: str, after: str, max_each: int = 100_000) -> TextDiff:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = SequenceMatcher(a=before_lines, b=after_lines, autojunk=False)
    added: list[str] = []
    removed: list[str] = []

    for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if operation in {"insert", "replace"}:
            added.extend(after_lines[new_start:new_end])
        if operation in {"delete", "replace"}:
            removed.extend(before_lines[old_start:old_end])

    added_text, added_truncated = _truncate("\n".join(added), max_each)
    removed_text, removed_truncated = _truncate("\n".join(removed), max_each)
    return TextDiff(
        added_text=added_text,
        removed_text=removed_text,
        truncated=added_truncated or removed_truncated,
    )
