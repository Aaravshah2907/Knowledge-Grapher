"""Scan markdown vault and produce ParsedNote objects."""

from __future__ import annotations

from pathlib import Path

from kgrapher.graph.model import ParsedNote
from kgrapher.parser.frontmatter import _as_str_list, _normalize_id, parse_file
from kgrapher.parser.latex import extract_formulas
from kgrapher.parser.wikilinks import extract_wikilinks


def scan_notes(notes_path: Path) -> list[ParsedNote]:
    notes: list[ParsedNote] = []
    for path in sorted(notes_path.rglob("*.md")):
        note = parse_note(path)
        if note:
            notes.append(note)
    return notes


def parse_note(path: Path) -> ParsedNote | None:
    meta, body = parse_file(str(path))
    default_id = _normalize_id(path.stem)
    note_id = _normalize_id(str(meta.get("id", default_id)))
    title = str(meta.get("title", path.stem.replace("-", " ").title()))
    tags = _as_str_list(meta.get("tags"))
    aliases = _as_str_list(meta.get("aliases"))
    depends_on = _as_str_list(meta.get("depends_on")) + _as_str_list(
        meta.get("requires")
    )
    wikilinks = extract_wikilinks(body)
    formulas = extract_formulas(body)
    card_formula = _card_formula_from_meta(meta)

    return ParsedNote(
        id=note_id,
        title=title,
        path=path,
        tags=tags,
        aliases=aliases,
        depends_on=depends_on,
        wikilinks=wikilinks,
        formulas=formulas,
        card_formula=card_formula,
        body=body,
    )


def _card_formula_from_meta(meta: dict) -> str | None:
    raw = meta.get("card_formula") or meta.get("key_formula")
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
    else:
        text = str(raw).strip()
    return text or None


def build_id_index(notes: list[ParsedNote]) -> dict[str, ParsedNote]:
    index: dict[str, ParsedNote] = {}
    for note in notes:
        index[note.id] = note
        for alias in note.aliases:
            index[alias] = note
    return index


def resolve_target(raw: str, index: dict[str, ParsedNote]) -> str | None:
    key = _normalize_id(raw)
    if key in index:
        return index[key].id
    return None
