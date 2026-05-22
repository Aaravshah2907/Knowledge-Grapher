"""Extract Obsidian-style [[wikilinks]]."""

from __future__ import annotations

import re

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")


def extract_wikilinks(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        target = _normalize_id(match.group(1).strip())
        if target and target not in seen:
            seen.add(target)
            result.append(target)
    return result


def _normalize_id(raw: str) -> str:
    return raw.lower().replace(" ", "-")
