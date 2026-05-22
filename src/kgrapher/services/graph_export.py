"""Export knowledge graph to HTML via pyvis."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
from pyvis.network import Network

from kgrapher.config import AppConfig
from kgrapher.graph.builder import build_graph
from kgrapher.graph.model import Edge, EdgeType, ParsedNote
from kgrapher.storage.db import connect
from kgrapher.storage.repository import Repository


def export_graph_html(config: AppConfig, output: Path) -> Path:
    conn = connect(config.db_path)
    repo = Repository(conn)
    concepts = repo.list_concepts()
    edges_raw = repo.list_edges()

    notes = [
        ParsedNote(
            id=c["id"],
            title=c["title"],
            path=Path(c["path"]),
            tags=[],
        )
        for c in concepts
    ]
    edges = [
        Edge(
            src=e["src"],
            dst=e["dst"],
            type=EdgeType.HARD if e["type"] == "hard" else EdgeType.SOFT,
        )
        for e in edges_raw
    ]
    g = build_graph(notes, edges)

    net = Network(directed=True, height="750px", width="100%", bgcolor="#ffffff")
    for node in g.nodes():
        data = g.nodes[node]
        cent = next((c["centrality"] for c in concepts if c["id"] == node), 0)
        size = 10 + 40 * float(cent)
        net.add_node(
            node,
            label=data.get("title", node),
            title=f"{data.get('title', node)}\nPageRank: {cent:.4f}",
            size=size,
        )
    for u, v, data in g.edges(data=True):
        color = "#c0392b" if data.get("type") == "hard" else "#7f8c8d"
        net.add_edge(u, v, color=color, arrows="to")
    net.set_options(
        '{"physics": {"enabled": true, "barnesHut": {"gravitationalConstant": -8000}}}'
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output))
    return output
