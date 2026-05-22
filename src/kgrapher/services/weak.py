"""Weak-link analysis from recall performance and graph structure."""

from __future__ import annotations

from kgrapher.config import AppConfig
from kgrapher.graph.builder import build_graph
from kgrapher.graph.centrality import compute_pagerank
from kgrapher.srs.scheduler import rolling_accuracy
from kgrapher.storage.db import connect
from kgrapher.storage.repository import Repository


def analyze_weak_links(config: AppConfig) -> list[dict]:
    conn = connect(config.db_path)
    repo = Repository(conn)
    concepts = {c["id"]: c for c in repo.list_concepts()}
    edges = repo.list_edges("hard")
    window = config.scheduler.weak_window

    # build minimal graph for prerequisite centrality
    from kgrapher.graph.model import Edge, EdgeType, ParsedNote

    notes = [
        ParsedNote(id=cid, title=c["title"], path=c["path"], tags=[])
        for cid, c in concepts.items()
    ]
    edge_objs = [
        Edge(src=e["src"], dst=e["dst"], type=EdgeType.HARD) for e in edges
    ]
    g = build_graph(notes, edge_objs)
    centralities = compute_pagerank(g)

    # map: concept -> max centrality of its hard prerequisites
    prereq_cent: dict[str, float] = {cid: 0.0 for cid in concepts}
    for e in edges:
        src, dst = e["src"], e["dst"]
        prereq_cent[dst] = max(prereq_cent[dst], centralities.get(src, 0.0))

    weak: list[dict] = []
    for cid, concept in concepts.items():
        reviews = repo.recent_reviews_for_concept(cid, limit=window)
        grades = [int(r["grade"]) for r in reviews]
        acc = rolling_accuracy(grades)
        if acc is None:
            continue
        if acc >= 0.6:
            continue
        out_degree = sum(1 for e in edges if e["src"] == cid)
        weak.append(
            {
                "id": cid,
                "title": concept["title"],
                "accuracy": acc,
                "reviews": len(grades),
                "centrality": centralities.get(cid, 0.0),
                "prereq_centrality": prereq_cent.get(cid, 0.0),
                "unlocks": out_degree,
            }
        )

    weak.sort(
        key=lambda x: (1 - x["accuracy"]) * (1 + x["centrality"] + x["prereq_centrality"]),
        reverse=True,
    )
    return weak
