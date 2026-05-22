"""Parse YAML frontmatter and dependency fields."""

from __future__ import annotations

from typing import Any

import frontmatter


def _normalize_id(raw: str) -> str:
    return raw.lower().replace(" ", "-").strip()


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_normalize_id(value)]
    if isinstance(value, list):
        return [_normalize_id(str(v)) for v in value if v]
    return []


def parse_file(path: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(path)
    return dict(post.metadata), post.content
