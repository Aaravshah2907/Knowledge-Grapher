from kgrapher.web.math import looks_like_latex, prepare_math_html, wrap_display_math


def test_wrap_display_math_adds_delimiters():
    assert wrap_display_math(r"\mu_t") == r"$$ \mu_t $$"


def test_wrap_display_math_preserves_existing():
    tex = r"$$ dX_t = \mu_t\,dt $$"
    assert wrap_display_math(tex) == tex


def test_wrap_display_math_leaves_prose_plain():
    assert wrap_display_math("(+2 more formulas in notes)") == "(+2 more formulas in notes)"


def test_looks_like_latex_plain_question():
    assert not looks_like_latex("What is Itô's Lemma?")


def test_looks_like_latex_command():
    assert looks_like_latex(r"\int_0^t dW_s")


def test_prepare_math_html_wraps_bare_latex():
    out = str(prepare_math_html(r"\int_0^t dW_s"))
    assert "$$" in out
    assert r"\int_0^t" in out


def test_prepare_math_html_preserves_prose_spaces():
    out = str(prepare_math_html("What is Brownian Motion?"))
    assert "$$" not in out
    assert "What is Brownian Motion?" in out


def test_prepare_math_html_mixed_lines():
    text = r"$$ \int_0^t dW_s $$" + "\n(+2 more formulas in notes)"
    out = str(prepare_math_html(text))
    assert "(+2 more formulas in notes)" in out
    assert "$$" in out
