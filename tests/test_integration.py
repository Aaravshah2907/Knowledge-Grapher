import tempfile
from pathlib import Path

from kgrapher.config import AppConfig
from kgrapher.services.cards import generate_cards
from kgrapher.services.scan import run_scan
from kgrapher.storage.db import init_db
from kgrapher.storage.repository import Repository
from kgrapher.storage.db import connect

EXAMPLES = Path(__file__).parent.parent / "examples" / "sample-notes"


def test_full_scan_and_cards_pipeline():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        cfg = AppConfig(notes_path=EXAMPLES, db_path=db)
        init_db(db)
        result = run_scan(cfg)
        assert result["notes"] == 3
        assert result["edges"] >= 3
        n = generate_cards(cfg)
        assert n == 3
        repo = Repository(connect(db))
        assert repo.card_count() == 3
