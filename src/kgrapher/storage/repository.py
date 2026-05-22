"""Data access layer for concepts, edges, cards, and reviews."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from kgrapher.graph.model import ConceptNode, Edge, EdgeType, ParsedNote


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO graph_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_meta(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM graph_meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def upsert_concepts(self, notes: list[ParsedNote], centralities: dict[str, float]) -> None:
        for note in notes:
            self.conn.execute(
                """
                INSERT INTO concepts (id, title, path, tags, centrality, formulas_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    path = excluded.path,
                    tags = excluded.tags,
                    centrality = excluded.centrality,
                    formulas_json = excluded.formulas_json
                """,
                (
                    note.id,
                    note.title,
                    str(note.path),
                    json.dumps(note.tags),
                    centralities.get(note.id, 0.0),
                    json.dumps(note.formulas),
                ),
            )
        self.conn.commit()

    def replace_edges(self, edges: list[Edge]) -> None:
        self.conn.execute("DELETE FROM edges")
        for edge in edges:
            self.conn.execute(
                "INSERT OR IGNORE INTO edges (src, dst, type) VALUES (?, ?, ?)",
                (edge.src, edge.dst, edge.type.value),
            )
        self.conn.commit()

    def list_concepts(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, title, path, tags, centrality, formulas_json, priority_boost "
            "FROM concepts ORDER BY centrality DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_edges(self, edge_type: str | None = None) -> list[dict[str, Any]]:
        if edge_type:
            rows = self.conn.execute(
                "SELECT src, dst, type FROM edges WHERE type = ?", (edge_type,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT src, dst, type FROM edges").fetchall()
        return [dict(r) for r in rows]

    def get_concept(self, concept_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM concepts WHERE id = ?", (concept_id,)
        ).fetchone()
        return dict(row) if row else None

    def add_priority_boost(self, concept_id: str, boost: float) -> None:
        self.conn.execute(
            "UPDATE concepts SET priority_boost = priority_boost + ? WHERE id = ?",
            (boost, concept_id),
        )
        self.conn.commit()

    def reset_priority_boosts(self) -> None:
        self.conn.execute("UPDATE concepts SET priority_boost = 0")
        self.conn.commit()

    def create_card(self, concept_id: str, front: str, back: str) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO cards (concept_id, front, back, next_due)
            VALUES (?, ?, ?, ?)
            """,
            (concept_id, front, back, _now_iso()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_cards_for_concept(self, concept_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM cards WHERE concept_id = ?", (concept_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def list_all_cards(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM cards").fetchall()
        return [dict(r) for r in rows]

    def update_card_sm2(
        self,
        card_id: int,
        interval_days: float,
        repetitions: int,
        easiness: float,
        next_due: str,
    ) -> None:
        self.conn.execute(
            """
            UPDATE cards SET interval_days = ?, repetitions = ?, easiness = ?, next_due = ?
            WHERE id = ?
            """,
            (interval_days, repetitions, easiness, next_due, card_id),
        )
        self.conn.commit()

    def record_review(
        self, card_id: int, grade: int, elapsed_ms: int = 0
    ) -> None:
        self.conn.execute(
            "INSERT INTO reviews (card_id, grade, reviewed_at, elapsed_ms) VALUES (?, ?, ?, ?)",
            (card_id, grade, _now_iso(), elapsed_ms),
        )
        self.conn.commit()

    def recent_reviews_for_concept(
        self, concept_id: str, limit: int = 7
    ) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT r.grade, r.reviewed_at
            FROM reviews r
            JOIN cards c ON c.id = r.card_id
            WHERE c.concept_id = ?
            ORDER BY r.reviewed_at DESC
            LIMIT ?
            """,
            (concept_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def card_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM cards").fetchone()
        return int(row["n"])
