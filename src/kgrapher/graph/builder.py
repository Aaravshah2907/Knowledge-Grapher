"""Build directed dependency graph from parsed notes."""

from __future__ import annotations

import networkx as nx

from kgrapher.graph.model import Edge, EdgeType, ParsedNote
from kgrapher.parser.scanner import build_id_index, resolve_target


def build_edges(notes: list[ParsedNote]) -> tuple[list[Edge], list[str]]:
    """Return edges (A -> B means B depends on A) and orphan link warnings."""
    index = build_id_index(notes)
    known_ids = {n.id for n in notes}
    edges: list[Edge] = []
    seen: set[tuple[str, str, EdgeType]] = set()
    orphans: list[str] = []

    def add_edge(src: str, dst: str, edge_type: EdgeType) -> None:
        if src == dst or src not in known_ids or dst not in known_ids:
            return
        key = (src, dst, edge_type)
        if key in seen:
            return
        # hard wins: if soft exists, still add hard separately by type
        seen.add(key)
        edges.append(Edge(src=src, dst=dst, type=edge_type))

    for note in notes:
        for dep in note.depends_on:
            src = resolve_target(dep, index) or dep
            if src not in known_ids:
                orphans.append(f"{note.id} depends_on missing: {dep}")
                continue
            add_edge(src, note.id, EdgeType.HARD)

        for link in note.wikilinks:
            src = resolve_target(link, index)
            if not src:
                orphans.append(f"{note.id} wikilink missing: {link}")
                continue
            if src == note.id:
                continue
            # skip if hard edge already present
            hard_key = (src, note.id, EdgeType.HARD)
            if hard_key in seen:
                continue
            add_edge(src, note.id, EdgeType.SOFT)

    return edges, orphans


def build_graph(
    notes: list[ParsedNote], edges: list[Edge] | None = None
) -> nx.DiGraph:
    if edges is None:
        edges, _ = build_edges(notes)
    g = nx.DiGraph()
    for note in notes:
        g.add_node(note.id, title=note.title, path=str(note.path))
    for edge in edges:
        g.add_edge(edge.src, edge.dst, type=edge.type.value)
    return g


def hard_subgraph(g: nx.DiGraph) -> nx.DiGraph:
    h = nx.DiGraph()
    h.add_nodes_from(g.nodes(data=True))
    for u, v, data in g.edges(data=True):
        if data.get("type") == EdgeType.HARD.value:
            h.add_edge(u, v)
    return h
