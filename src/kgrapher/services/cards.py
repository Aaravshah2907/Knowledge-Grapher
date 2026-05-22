"""Flashcard generation from parsed concepts."""

from __future__ import annotations

from kgrapher.config import AppConfig
from kgrapher.graph.model import ParsedNote
from kgrapher.parser.scanner import scan_notes
from kgrapher.storage.db import connect
from kgrapher.storage.repository import Repository
from kgrapher.web.math import wrap_display_math


def pick_card_back(note: ParsedNote) -> str:
    """Choose flashcard answer text: explicit frontmatter > first extracted formula."""
    if note.card_formula:
        return wrap_display_math(note.card_formula)
    if note.formulas:
        back = wrap_display_math(note.formulas[0])
        if len(note.formulas) > 1:
            back += f"\n\n(+{len(note.formulas) - 1} more formulas in notes)"
        return back
    return f"See note: {note.path.name}"


def generate_cards(config: AppConfig, overwrite: bool = False) -> int:
    notes_path = config.require_notes_path()
    notes = scan_notes(notes_path)
    conn = connect(config.db_path)
    repo = Repository(conn)
    created = 0

    for note in notes:
        existing = repo.list_cards_for_concept(note.id)
        if existing and not overwrite:
            continue
        front = f"What is {note.title}?"
        repo.create_card(note.id, front, pick_card_back(note))
        created += 1

    return created
