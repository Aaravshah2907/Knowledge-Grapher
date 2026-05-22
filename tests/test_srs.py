from datetime import datetime, timedelta, timezone

from kgrapher.srs.scheduler import apply_review, card_priority, rolling_accuracy, sort_due_cards
from kgrapher.srs.sm2 import SM2State, update_sm2
from kgrapher.config import SchedulerConfig


def test_sm2_pass_increases_interval():
    state = SM2State(interval_days=1, repetitions=1, easiness=2.5)
    result = update_sm2(state, grade=4)
    assert not result.lapsed
    assert result.state.repetitions == 2
    assert result.state.interval_days >= 6


def test_sm2_lapse_resets_repetitions():
    state = SM2State(interval_days=10, repetitions=3, easiness=2.5)
    result = update_sm2(state, grade=2)
    assert result.lapsed
    assert result.state.repetitions == 0
    assert result.state.interval_days == 1.0


def test_rolling_accuracy():
    assert rolling_accuracy([5, 4, 2, 3]) == 0.75
    assert rolling_accuracy([]) is None


def test_card_priority_centrality():
    now = datetime.now(timezone.utc)
    due = now - timedelta(days=2)
    pri_low = card_priority(due, centrality=0.1, priority_boost=0, alpha=1.0)
    pri_high = card_priority(due, centrality=0.9, priority_boost=0, alpha=1.0)
    assert pri_high > pri_low


def test_sort_due_cards():
    now = datetime.now(timezone.utc)
    past = (now - timedelta(days=1)).isoformat()
    future = (now + timedelta(days=5)).isoformat()
    cards = [
        {"id": 1, "concept_id": "a", "next_due": past},
        {"id": 2, "concept_id": "b", "next_due": future},
    ]
    concepts = {
        "a": {"centrality": 0.1, "priority_boost": 0},
        "b": {"centrality": 0.9, "priority_boost": 0},
    }
    due = sort_due_cards(cards, concepts, SchedulerConfig(), now=now)
    assert len(due) == 1
    assert due[0]["concept_id"] == "a"
