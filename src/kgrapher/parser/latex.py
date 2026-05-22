"""Extract LaTeX formulas from markdown."""

from __future__ import annotations

import re

DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
ENV_RE = re.compile(
    r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.+?)\\end\{\1\}",
    re.DOTALL,
)


def extract_formulas(text: str) -> list[str]:
    formulas: list[str] = []
    seen: set[str] = set()

    def add(f: str) -> None:
        cleaned = " ".join(f.split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            formulas.append(cleaned)

    for m in DISPLAY_RE.finditer(text):
        add(m.group(1))
    for m in INLINE_RE.finditer(text):
        add(m.group(1))
    for m in ENV_RE.finditer(text):
        add(m.group(2))
    return formulas
