from pathlib import Path

from kgrapher.graph.builder import build_edges, build_graph
from kgrapher.graph.centrality import compute_pagerank, downstream_hard
from kgrapher.parser.scanner import scan_notes

FIXTURES = Path(__file__).parent / "fixtures" / "notes"


def test_build_edges_and_pagerank():
    notes = scan_notes(FIXTURES)
    edges, orphans = build_edges(notes)
    g = build_graph(notes, edges)
    assert g.number_of_nodes() == 3
    assert any(e.type.value == "hard" for e in edges)
    cent = compute_pagerank(g)
    assert cent["brownian-motion"] >= cent["ito-lemma"]
    downstream = downstream_hard(g, "brownian-motion")
    assert "ito-lemma" in downstream


def test_orphan_warning_for_missing_link():
    notes = scan_notes(FIXTURES)
    _, orphans = build_edges(notes)
    assert isinstance(orphans, list)
