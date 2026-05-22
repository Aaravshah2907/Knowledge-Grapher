"""Graph domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EdgeType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass
class ParsedNote:
    id: str
    title: str
    path: Path
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    wikilinks: list[str] = field(default_factory=list)
    formulas: list[str] = field(default_factory=list)
    body: str = ""


@dataclass
class Edge:
    src: str
    dst: str
    type: EdgeType


@dataclass
class ConceptNode:
    id: str
    title: str
    path: Path
    tags: list[str]
    formulas: list[str]
    centrality: float = 0.0
