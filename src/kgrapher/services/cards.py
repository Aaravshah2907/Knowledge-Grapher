"""Flashcard generation from parsed concepts."""

from __future__ import annotations

from kgrapher.config import AppConfig
from kgrapher.parser.scanner import scan_notes
from kgrapher.storage.db import connect
from kgrapher.storage.repository import Repository


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
        if note.formulas:
            back = note.formulas[0]
            if len(note.formulas) > 1:
                back += f"\n\n(+{len(note.formulas) - 1} more formulas in notes)"
        else:
            back = f"See note: {note.path.name}"
        repo.create_card(note.id, front, back)
        created += 1

    return created
