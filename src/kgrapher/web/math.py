"""Prepare note/card LaTeX for KaTeX rendering in HTML templates."""

from __future__ import annotations

import re

from markupsafe import Markup, escape

# Already wrapped in display or inline math delimiters
_HAS_DISPLAY = re.compile(r"\$\$.+?\$\$", re.DOTALL)
_HAS_INLINE = re.compile(r"(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)", re.DOTALL)

# Heuristic: distinguish prose from LaTeX (avoid wrapping English in $$ math mode)
_LATEX_COMMAND = re.compile(r"\\[a-zA-Z@]+")
_LATEX_CONSTRUCT = re.compile(
    r"\\(?:frac|int|sum|partial|sqrt|cdot|times|left|right|begin|end)\b"
)
_SUBSCRIPT = re.compile(r"[A-Za-z0-9][\^_]\{?[A-Za-z0-9]")
# Words with spaces = prose, not math (unless already in delimiters)
_HAS_WORD_SPACE = re.compile(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}")


def looks_like_latex(text: str) -> bool:
    """True if text should be rendered as math, not plain prose."""
    stripped = text.strip()
    if not stripped:
        return False
    if _HAS_DISPLAY.search(stripped) or _HAS_INLINE.search(stripped):
        return True
    # Multi-word English sentences stay plain text (spaces preserved in HTML)
    if _HAS_WORD_SPACE.search(stripped) and not _LATEX_COMMAND.search(stripped):
        return False
    if _LATEX_COMMAND.search(stripped) or _LATEX_CONSTRUCT.search(stripped):
        return True
    if _SUBSCRIPT.search(stripped):
        return True
    return False


def _prepare_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if _HAS_DISPLAY.search(line) or _HAS_INLINE.search(line):
        return str(escape(line))
    if looks_like_latex(line):
        return str(escape(f"$$ {line} $$"))
    return str(escape(line))


def prepare_math_html(text: str) -> Markup:
    """Escape HTML; wrap only LaTeX lines in $$ so prose keeps normal spaces."""
    if not text:
        return Markup("")
    lines = text.splitlines()
    rendered = [_prepare_line(line) for line in lines]
    # Drop empty trailing lines but keep intentional blank lines between blocks
    while rendered and not rendered[-1]:
        rendered.pop()
    return Markup("<br>\n".join(rendered))


def wrap_display_math(text: str) -> str:
    """Wrap raw LaTeX in $$ for storage (card backs from formula extractor)."""
    stripped = text.strip()
    if not stripped:
        return ""
    if _HAS_DISPLAY.search(stripped) or _HAS_INLINE.search(stripped):
        return stripped
    if not looks_like_latex(stripped):
        return stripped
    return f"$$ {stripped} $$"
