"""SQLite schema and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    centrality REAL DEFAULT 0.0,
    formulas_json TEXT DEFAULT '[]',
    priority_boost REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('hard', 'soft')),
    PRIMARY KEY (src, dst, type),
    FOREIGN KEY (src) REFERENCES concepts(id),
    FOREIGN KEY (dst) REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    interval_days REAL DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    easiness REAL DEFAULT 2.5,
    next_due TEXT,
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    grade INTEGER NOT NULL,
    reviewed_at TEXT NOT NULL,
    elapsed_ms INTEGER DEFAULT 0,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS graph_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> sqlite3.Connection:
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
