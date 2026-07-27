from __future__ import annotations

import re
from html.parser import HTMLParser

from app.config import settings


class ExtractionError(ValueError):
    pass


EXCLUDED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "main",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
}
NOISE_MARKERS = {
    "advert",
    "advertisement",
    "breadcrumb",
    "cookie",
    "consent",
    "modal",
    "newsletter",
    "popup",
    "share",
    "social",
}
SPACE_RE = re.compile(r"[ \t\u3000]+")
BLANK_RE = re.compile(r"\n{3,}")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    @staticmethod
    def _is_noise(attrs: list[tuple[str, str | None]]) -> bool:
        values = {key.lower(): (value or "").lower() for key, value in attrs}
        if values.get("aria-hidden") == "true" or "hidden" in values:
            return True
        style = values.get("style", "").replace(" ", "")
        if "display:none" in style or "visibility:hidden" in style:
            return True
        identity = f"{values.get('id', '')} {values.get('class', '')}"
        tokens = set(re.split(r"[^a-z0-9]+", identity))
        return bool(tokens & NOISE_MARKERS)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self._skip_depth:
            if tag not in VOID_TAGS:
                self._skip_depth += 1
            return
        if tag in EXCLUDED_TAGS or self._is_noise(attrs):
            self._skip_depth = 1
            return
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._skip_depth and tag.lower() in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag.lower() in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def normalize_text(value: str) -> str:
    lines: list[str] = []
    for raw_line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = SPACE_RE.sub(" ", raw_line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return BLANK_RE.sub("\n\n", "\n".join(lines)).strip()


def extract_visible_text(html: str, max_chars: int | None = None) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        raise ExtractionError("ページ本文を解析できませんでした。") from exc

    text = normalize_text(parser.text())
    if not text:
        raise ExtractionError(
            "本文を取得できませんでした。JavaScriptが必要なページの可能性があります。"
        )

    limit = max_chars or settings.max_extracted_chars
    if len(text) > limit:
        raise ExtractionError("抽出した本文が保存上限を超えています。")
    return text
