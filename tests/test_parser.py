from pathlib import Path

from kgrapher.parser.latex import extract_formulas
from kgrapher.parser.scanner import scan_notes
from kgrapher.parser.wikilinks import extract_wikilinks

FIXTURES = Path(__file__).parent / "fixtures" / "notes"


def test_extract_wikilinks():
    text = "See [[brownian-motion]] and [[stochastic-integral|integral]]."
    assert extract_wikilinks(text) == ["brownian-motion", "stochastic-integral"]


def test_extract_formulas():
    text = r"Inline $E[X]$ and display $$\int_0^t dW_s$$"
    formulas = extract_formulas(text)
    assert "E[X]" in formulas[0] or any("E[X]" in f for f in formulas)
    assert any("int_0" in f for f in formulas)


def test_scan_fixture_vault():
    notes = scan_notes(FIXTURES)
    ids = {n.id for n in notes}
    assert "brownian-motion" in ids
    assert "ito-lemma" in ids
    ito = next(n for n in notes if n.id == "ito-lemma")
    assert "brownian-motion" in ito.depends_on
    assert "brownian-motion" in ito.wikilinks
    assert len(ito.formulas) >= 1
