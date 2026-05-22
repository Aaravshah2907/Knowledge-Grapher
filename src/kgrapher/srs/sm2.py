"""SuperMemo SM-2 algorithm."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SM2State:
    interval_days: float = 0.0
    repetitions: int = 0
    easiness: float = 2.5


@dataclass
class SM2Result:
    state: SM2State
    next_due: datetime
    lapsed: bool


def update_sm2(state: SM2State, grade: int) -> SM2Result:
    """grade 0-5; lapse when grade < 3."""
    ef = state.easiness
    reps = state.repetitions
    interval = state.interval_days
    lapsed = grade < 3

    if lapsed:
        reps = 0
        interval = 1.0
    else:
        if reps == 0:
            interval = 1.0
        elif reps == 1:
            interval = 6.0
        else:
            interval = round(interval * ef)
        reps += 1

    ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if ef < 1.3:
        ef = 1.3

    next_due = datetime.now(timezone.utc) + timedelta(days=interval)
    return SM2Result(
        state=SM2State(interval_days=interval, repetitions=reps, easiness=ef),
        next_due=next_due,
        lapsed=lapsed,
    )
