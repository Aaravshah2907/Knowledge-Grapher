"""User configuration under ~/.kgrapher/."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".kgrapher"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_DB_PATH = DEFAULT_CONFIG_DIR / "kgrapher.db"


@dataclass
class SchedulerConfig:
    alpha: float = 1.0  # centrality weight in priority
    beta: float = 0.5  # cascade boost multiplier
    weak_window: int = 7  # rolling review window for weak-link report


@dataclass
class AppConfig:
    notes_path: Path | None = None
    db_path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text()) or {}
        sched = data.get("scheduler", {})
        return cls(
            notes_path=Path(data["notes_path"]) if data.get("notes_path") else None,
            db_path=Path(data.get("db_path", DEFAULT_DB_PATH)),
            scheduler=SchedulerConfig(
                alpha=float(sched.get("alpha", 1.0)),
                beta=float(sched.get("beta", 0.5)),
                weak_window=int(sched.get("weak_window", 7)),
            ),
        )

    def save(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "notes_path": str(self.notes_path) if self.notes_path else None,
            "db_path": str(self.db_path),
            "scheduler": {
                "alpha": self.scheduler.alpha,
                "beta": self.scheduler.beta,
                "weak_window": self.scheduler.weak_window,
            },
        }
        path.write_text(yaml.dump(payload, default_flow_style=False))

    def require_notes_path(self) -> Path:
        if not self.notes_path:
            raise ValueError(
                "Notes path not set. Run: kgrapher init /path/to/your/notes"
            )
        if not self.notes_path.exists():
            raise ValueError(f"Notes path does not exist: {self.notes_path}")
        return self.notes_path
