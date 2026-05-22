"""PageRank and downstream queries."""

from __future__ import annotations

import networkx as nx
from networkx.algorithms.link_analysis.pagerank_alg import _pagerank_python

from kgrapher.graph.builder import hard_subgraph


def compute_pagerank(g: nx.DiGraph, alpha: float = 0.85) -> dict[str, float]:
    """PageRank on hard-dependency edges; fall back to full graph if empty."""
    h = hard_subgraph(g)
    if h.number_of_edges() == 0:
        h = g
    if h.number_of_nodes() == 0:
        return {}
    if h.number_of_edges() == 0:
        n = h.number_of_nodes()
        return {node: 1.0 / n for node in h.nodes()}
    # Edges are prerequisite -> dependent; reverse so PageRank rewards foundations
    h_rev = h.reverse(copy=False)
    scores = _pagerank_python(h_rev, alpha=alpha, max_iter=200)
    return scores


def downstream_hard(g: nx.DiGraph, node: str) -> set[str]:
    h = hard_subgraph(g)
    if node not in h:
        return set()
    return nx.descendants(h, node)
