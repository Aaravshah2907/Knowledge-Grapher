from pathlib import Path

from kgrapher.graph.model import ParsedNote
from kgrapher.parser.scanner import parse_note
from kgrapher.services.cards import pick_card_back

FIXTURES = Path(__file__).parent / "fixtures" / "notes"


def test_pick_card_back_uses_first_display_math():
    note = parse_note(FIXTURES / "ito-lemma.md")
    assert note is not None
    back = pick_card_back(note)
    assert "dX_t" in back and "mu_t" in back


def test_pick_card_back_prefers_card_formula():
    note = ParsedNote(
        id="test",
        title="Test",
        path=Path("test.md"),
        formulas=[r"\alpha", r"\beta"],
        card_formula=r"\gamma",
    )
    back = pick_card_back(note)
    assert r"\gamma" in back
    assert "(+2 more" not in back
