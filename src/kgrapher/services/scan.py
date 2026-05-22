"""Scan notes vault and persist graph."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from kgrapher.config import AppConfig
from kgrapher.graph.builder import build_edges, build_graph
from kgrapher.graph.centrality import compute_pagerank
from kgrapher.parser.scanner import scan_notes
from kgrapher.storage.db import connect
from kgrapher.storage.repository import Repository

console = Console()


def _vault_checksum(notes_path: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(notes_path.rglob("*.md")):
        h.update(str(path).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def run_scan(config: AppConfig, strict: bool = False) -> dict:
    notes_path = config.require_notes_path()
    notes = scan_notes(notes_path)
    edges, orphans = build_edges(notes)
    g = build_graph(notes, edges)
    centralities = compute_pagerank(g)

    if strict and orphans:
        raise ValueError(
            "Orphan links found:\n" + "\n".join(orphans[:20])
            + (f"\n... and {len(orphans) - 20} more" if len(orphans) > 20 else "")
        )

    conn = connect(config.db_path)
    repo = Repository(conn)
    repo.upsert_concepts(notes, centralities)
    repo.replace_edges(edges)
    repo.set_meta("last_scan_at", datetime.now(timezone.utc).isoformat())
    repo.set_meta("vault_checksum", _vault_checksum(notes_path))
    repo.set_meta("graph_snapshot", json.dumps({"nodes": list(g.nodes()), "edges": list(g.edges())}))

    console.print(f"[green]Scanned[/green] {len(notes)} notes, {len(edges)} edges")
    if orphans:
        console.print(f"[yellow]Warnings:[/yellow] {len(orphans)} unresolved links")
        for msg in orphans[:5]:
            console.print(f"  - {msg}")
        if len(orphans) > 5:
            console.print(f"  ... {len(orphans) - 5} more")

    top = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:5]
    if top:
        console.print("[bold]Top foundational concepts (PageRank):[/bold]")
        for cid, score in top:
            title = next((n.title for n in notes if n.id == cid), cid)
            console.print(f"  {title} ({cid}): {score:.4f}")

    return {
        "notes": len(notes),
        "edges": len(edges),
        "orphans": len(orphans),
        "centralities": centralities,
    }
