"""Centrality-weighted scheduling and cascade on miss."""

from __future__ import annotations

from datetime import datetime, timezone

import networkx as nx

from kgrapher.config import SchedulerConfig
from kgrapher.graph.centrality import downstream_hard
from kgrapher.srs.sm2 import SM2State, update_sm2


def parse_due(iso: str | None) -> datetime:
    if not iso:
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def base_urgency(next_due: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if next_due.tzinfo is None:
        next_due = next_due.replace(tzinfo=timezone.utc)
    overdue_days = (now - next_due).total_seconds() / 86400.0
    return max(1.0, 1.0 + overdue_days)


def card_priority(
    next_due: datetime,
    centrality: float,
    priority_boost: float,
    alpha: float,
) -> float:
    urgency = base_urgency(next_due)
    return urgency * (1.0 + alpha * centrality) + priority_boost


def sort_due_cards(
    cards: list[dict],
    concepts: dict[str, dict],
    config: SchedulerConfig,
    now: datetime | None = None,
) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    due: list[tuple[float, dict]] = []
    for card in cards:
        due_at = parse_due(card.get("next_due"))
        if due_at > now:
            continue
        concept = concepts.get(card["concept_id"], {})
        cent = float(concept.get("centrality", 0))
        boost = float(concept.get("priority_boost", 0))
        pri = card_priority(due_at, cent, boost, config.alpha)
        due.append((pri, card))
    due.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in due]


def apply_review(
    state: SM2State,
    grade: int,
    graph: nx.DiGraph,
    concept_id: str,
    centrality: float,
    config: SchedulerConfig,
) -> tuple[SM2State, datetime, list[tuple[str, float]]]:
    """Return new state, next_due, and cascade boosts for descendants."""
    result = update_sm2(state, grade)
    boosts: list[tuple[str, float]] = []
    if result.lapsed:
        boost_amount = config.beta * centrality
        for desc in downstream_hard(graph, concept_id):
            boosts.append((desc, boost_amount))
    return result.state, result.next_due, boosts


def rolling_accuracy(grades: list[int]) -> float | None:
    if not grades:
        return None
    hits = sum(1 for g in grades if g >= 3)
    return hits / len(grades)
