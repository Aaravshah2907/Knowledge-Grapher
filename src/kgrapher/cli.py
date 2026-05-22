"""CLI entry point for kgrapher."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from kgrapher import __version__
from kgrapher.config import DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_PATH, AppConfig

DEFAULT_GRAPH_HTML = DEFAULT_CONFIG_DIR / "graph-export.html"
from kgrapher.graph.builder import build_edges, build_graph
from kgrapher.graph.model import Edge, EdgeType, ParsedNote
from kgrapher.services.cards import generate_cards
from kgrapher.services.graph_export import export_graph_html
from kgrapher.services.scan import run_scan
from kgrapher.services.weak import analyze_weak_links
from kgrapher.srs.scheduler import apply_review, sort_due_cards
from kgrapher.srs.sm2 import SM2State
from kgrapher.storage.db import init_db
from kgrapher.storage.repository import Repository

app = typer.Typer(
    name="kgrapher",
    help="Local knowledge graph for exam prep with centrality-weighted spaced repetition.",
    no_args_is_help=True,
)
console = Console()


def _load_config() -> AppConfig:
    return AppConfig.load()


def _repo() -> Repository:
    cfg = _load_config()
    init_db(cfg.db_path)
    from kgrapher.storage.db import connect

    return Repository(connect(cfg.db_path))


def _load_graph_for_srs(cfg: AppConfig):
    repo = _repo()
    concepts = repo.list_concepts()
    edges_raw = repo.list_edges("hard")
    notes = [
        ParsedNote(id=c["id"], title=c["title"], path=Path(c["path"]))
        for c in concepts
    ]
    edges = [Edge(src=e["src"], dst=e["dst"], type=EdgeType.HARD) for e in edges_raw]
    return build_graph(notes, edges), {c["id"]: c for c in concepts}


@app.command()
def version() -> None:
    """Show package version."""
    console.print(f"kgrapher {__version__}")


@app.command()
def init(
    notes_path: Path = typer.Argument(
        ...,
        help="Path to your markdown notes vault",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Initialize config and database."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg = AppConfig(notes_path=notes_path.resolve())
    init_db(cfg.db_path)
    cfg.save()
    console.print(f"[green]Initialized[/green] config at {DEFAULT_CONFIG_PATH}")
    console.print(f"Notes: {cfg.notes_path}")
    console.print(f"Database: {cfg.db_path}")


@app.command()
def scan(
    strict: bool = typer.Option(False, help="Fail if orphan wikilinks exist"),
) -> None:
    """Parse notes, rebuild graph, refresh PageRank."""
    cfg = _load_config()
    init_db(cfg.db_path)
    run_scan(cfg, strict=strict)


cards_app = typer.Typer(help="Flashcard management")
app.add_typer(cards_app, name="cards")


@cards_app.command("generate")
def cards_generate(
    overwrite: bool = typer.Option(False, help="Create cards even if they exist"),
) -> None:
    """Generate draft flashcards from note titles and LaTeX."""
    cfg = _load_config()
    n = generate_cards(cfg, overwrite=overwrite)
    console.print(f"[green]Created[/green] {n} cards")


@app.command()
def review(
    limit: int = typer.Option(20, help="Max cards per session"),
) -> None:
    """Run an interactive spaced-repetition review session."""
    cfg = _load_config()
    repo = _repo()
    graph, concepts = _load_graph_for_srs(cfg)
    all_cards = repo.list_all_cards()
    due = sort_due_cards(all_cards, concepts, cfg.scheduler)[:limit]

    if not due:
        console.print("[green]No cards due.[/green] Great work!")
        raise typer.Exit(0)

    console.print(Panel(f"Review session — {len(due)} cards", style="bold blue"))
    reviewed = 0

    for card in due:
        concept = concepts.get(card["concept_id"], {})
        console.print()
        console.print(Panel(card["front"], title="Front", border_style="cyan"))
        Prompt.ask("Press Enter to reveal", default="")
        console.print(Panel(card["back"], title="Back", border_style="green"))
        grade = IntPrompt.ask(
            "Grade (0-5, <3 = miss)",
            choices=["0", "1", "2", "3", "4", "5"],
            default="3",
        )

        state = SM2State(
            interval_days=float(card["interval_days"]),
            repetitions=int(card["repetitions"]),
            easiness=float(card["easiness"]),
        )
        cent = float(concept.get("centrality", 0))
        new_state, next_due, boosts = apply_review(
            state,
            grade,
            graph,
            card["concept_id"],
            cent,
            cfg.scheduler,
        )
        repo.update_card_sm2(
            card["id"],
            new_state.interval_days,
            new_state.repetitions,
            new_state.easiness,
            next_due.isoformat(),
        )
        repo.record_review(card["id"], grade)
        for desc_id, boost in boosts:
            repo.add_priority_boost(desc_id, boost)
            console.print(
                f"[yellow]Cascade:[/yellow] boosted downstream [bold]{desc_id}[/bold] +{boost:.3f}"
            )
        reviewed += 1

    console.print(f"\n[green]Reviewed {reviewed} cards.[/green]")


@app.command()
def weak() -> None:
    """Report weak links from recall performance and graph centrality."""
    cfg = _load_config()
    results = analyze_weak_links(cfg)
    if not results:
        console.print("[green]No weak links detected[/green] (need review history).")
        raise typer.Exit(0)

    table = Table(title="Weak Links")
    table.add_column("Concept")
    table.add_column("Accuracy", justify="right")
    table.add_column("Reviews", justify="right")
    table.add_column("Centrality", justify="right")
    table.add_column("Unlocks", justify="right")
    for row in results[:15]:
        table.add_row(
            f"{row['title']} ({row['id']})",
            f"{row['accuracy']:.0%}",
            str(row["reviews"]),
            f"{row['centrality']:.3f}",
            str(row["unlocks"]),
        )
    console.print(table)


graph_app = typer.Typer(help="Graph visualization")
app.add_typer(graph_app, name="graph")


@graph_app.command("export")
def graph_export(
    output: Path = typer.Option(
        DEFAULT_GRAPH_HTML,
        help="Output HTML path (default: ~/.kgrapher/graph-export.html)",
    ),
) -> None:
    """Export interactive graph to HTML."""
    cfg = _load_config()
    path = export_graph_html(cfg, output.resolve())
    console.print(f"[green]Exported[/green] graph to {path}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8765, help="Bind port"),
) -> None:
    """Start local web UI for graph and review."""
    import uvicorn

    from kgrapher.web.app import create_app

    cfg = _load_config()
    init_db(cfg.db_path)
    web_app = create_app(cfg)
    console.print(f"[green]Serving[/green] http://{host}:{port}")
    uvicorn.run(web_app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    app()
