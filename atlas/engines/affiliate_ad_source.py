"""ASPが発行するバナー広告ソースを安全に解析する。"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse


def _safe_http_url(value: str) -> str:
    url = value.strip()
    # もしもアフィリエイトなどが発行するプロトコル相対URLは、
    # デスクトップでの検証・サイトでの表示ともHTTPSへ統一する。
    if url.startswith("//"):
        url = f"https:{url}"
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


class _AdSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.href = ""
        self.images: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): str(value or "").strip() for key, value in attrs}
        if tag.lower() == "a" and not self.href:
            self.href = _safe_http_url(values.get("href", ""))
        if tag.lower() != "img":
            return
        src = _safe_http_url(values.get("src", ""))
        if not src:
            return
        try:
            width = max(0, int(values.get("width", "0") or 0))
            height = max(0, int(values.get("height", "0") or 0))
        except ValueError:
            width = 0
            height = 0
        self.images.append({"src": src, "width": width, "height": height})


def parse_ad_source(source: str) -> dict[str, Any]:
    """ASPのHTML広告ソース、または紹介URL単体を解析する。"""

    raw_source = source.strip()
    direct_url = _safe_http_url(raw_source)
    if direct_url:
        return {
            "href": direct_url,
            "banner_src": "",
            "banner_width": 0,
            "banner_height": 0,
            "tracking_pixel_src": "",
        }

    parser = _AdSourceParser()
    parser.feed(raw_source)
    banner = next(
        (image for image in parser.images if not (image["width"] <= 1 and image["height"] <= 1)),
        None,
    )
    tracking = next(
        (image for image in parser.images if image["width"] <= 1 and image["height"] <= 1),
        None,
    )
    if not parser.href or banner is None:
        raise ValueError(
            "広告ソースからリンク先とバナー画像を読み取れません。"
            "紹介URLだけを利用する案件は、httpから始まるURLを入力してください。"
        )
    return {
        "href": parser.href,
        "banner_src": banner["src"],
        "banner_width": banner["width"],
        "banner_height": banner["height"],
        "tracking_pixel_src": tracking["src"] if tracking else "",
    }
