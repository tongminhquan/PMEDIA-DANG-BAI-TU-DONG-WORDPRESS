from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from html import unescape
from pathlib import Path
import json
import re
from typing import Any, Iterable


@dataclass
class WebsitePostItem:
    post_id: int
    status: str
    title: str
    slug: str = ""
    link: str = ""
    date: str = ""
    modified: str = ""


@dataclass
class WebsitePostSnapshot:
    site_url: str
    synced_at: str
    total: int
    posts: list[WebsitePostItem] = field(default_factory=list)


class WebsitePostStore:
    def __init__(self, store_path: str | Path = "config/website_posts.json", max_sites: int = 20):
        self.store_path = Path(store_path)
        self.max_sites = max_sites

    def load_snapshots(self) -> list[WebsitePostSnapshot]:
        if not self.store_path.exists():
            return []
        try:
            raw = json.loads(self.store_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            return []
        if not isinstance(raw, list):
            return []
        return [_snapshot_from_dict(item) for item in raw if isinstance(item, dict)]

    def get_snapshot(self, site_url: str) -> WebsitePostSnapshot | None:
        key = _site_key(site_url)
        for snapshot in self.load_snapshots():
            if _site_key(snapshot.site_url) == key:
                return snapshot
        return None

    def save_snapshot(
        self,
        site_url: str,
        payloads: Iterable[dict[str, Any]],
        synced_at: str | None = None,
    ) -> WebsitePostSnapshot:
        normalized_url = site_url.strip().rstrip("/")
        posts = [_post_from_payload(payload) for payload in payloads if isinstance(payload, dict)]
        snapshot = WebsitePostSnapshot(
            site_url=normalized_url,
            synced_at=synced_at or datetime.now().isoformat(timespec="seconds"),
            total=len(posts),
            posts=posts,
        )
        snapshots = [
            item for item in self.load_snapshots() if _site_key(item.site_url) != _site_key(normalized_url)
        ]
        self._write_snapshots([snapshot, *snapshots][: self.max_sites])
        return snapshot

    def _write_snapshots(self, snapshots: list[WebsitePostSnapshot]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        payload = [asdict(snapshot) for snapshot in snapshots]
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.store_path)


def _post_from_payload(payload: dict[str, Any]) -> WebsitePostItem:
    return WebsitePostItem(
        post_id=_as_int(payload.get("id")),
        status=str(payload.get("status") or ""),
        title=_payload_text(payload.get("title")),
        slug=str(payload.get("slug") or ""),
        link=str(payload.get("link") or ""),
        date=str(payload.get("date") or ""),
        modified=str(payload.get("modified") or ""),
    )


def _snapshot_from_dict(data: dict[str, Any]) -> WebsitePostSnapshot:
    posts = [
        WebsitePostItem(
            post_id=_as_int(item.get("post_id")),
            status=str(item.get("status") or ""),
            title=str(item.get("title") or ""),
            slug=str(item.get("slug") or ""),
            link=str(item.get("link") or ""),
            date=str(item.get("date") or ""),
            modified=str(item.get("modified") or ""),
        )
        for item in data.get("posts", [])
        if isinstance(item, dict)
    ]
    return WebsitePostSnapshot(
        site_url=str(data.get("site_url") or "").rstrip("/"),
        synced_at=str(data.get("synced_at") or ""),
        total=len(posts),
        posts=posts,
    )


def _payload_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("raw") or value.get("rendered") or ""
    text = re.sub(r"<[^>]+>", "", str(value or ""))
    return unescape(text).strip()


def _site_key(site_url: str) -> str:
    return site_url.strip().rstrip("/").casefold()


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
