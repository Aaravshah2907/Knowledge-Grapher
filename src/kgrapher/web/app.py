"""FastAPI local web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from kgrapher.config import AppConfig
from kgrapher.graph.builder import build_graph
from kgrapher.graph.model import Edge, EdgeType, ParsedNote
from kgrapher.services.graph_export import export_graph_html
from kgrapher.services.scan import run_scan
from kgrapher.services.weak import analyze_weak_links
from kgrapher.srs.scheduler import apply_review, sort_due_cards
from kgrapher.srs.sm2 import SM2State
from kgrapher.storage.db import connect, init_db
from kgrapher.storage.repository import Repository
from kgrapher.web.math import prepare_math_html

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
TEMPLATES.env.filters["math_html"] = prepare_math_html


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title="Knowledge Grapher", docs_url=None, redoc_url=None)
    graph_html = Path.home() / ".kgrapher" / "graph.html"

    def repo() -> Repository:
        init_db(config.db_path)
        return Repository(connect(config.db_path))

    def load_graph():
        r = repo()
        concepts = r.list_concepts()
        edges_raw = r.list_edges("hard")
        notes = [
            ParsedNote(id=c["id"], title=c["title"], path=Path(c["path"]))
            for c in concepts
        ]
        edges = [Edge(src=e["src"], dst=e["dst"], type=EdgeType.HARD) for e in edges_raw]
        g = build_graph(notes, edges)
        return g, {c["id"]: c for c in concepts}

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        r = repo()
        concepts = r.list_concepts()
        cards = r.list_all_cards()
        _, concept_map = load_graph()
        due = sort_due_cards(cards, concept_map, config.scheduler)
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "concepts": len(concepts),
                "cards": len(cards),
                "due": len(due),
            },
        )

    @app.post("/scan")
    async def scan_action():
        run_scan(config)
        return RedirectResponse("/", status_code=303)

    @app.get("/graph", response_class=HTMLResponse)
    async def graph_page(request: Request):
        return TEMPLATES.TemplateResponse(request, "graph.html", {})

    @app.get("/graph/view")
    async def graph_view_file():
        export_graph_html(config, graph_html)
        return FileResponse(graph_html, media_type="text/html")

    @app.get("/weak", response_class=HTMLResponse)
    async def weak_view(request: Request):
        weak = analyze_weak_links(config)
        return TEMPLATES.TemplateResponse(
            request,
            "weak.html",
            {"weak": weak},
        )

    @app.get("/review", response_class=HTMLResponse)
    async def review_view(request: Request):
        r = repo()
        graph, concept_map = load_graph()
        cards = r.list_all_cards()
        due = sort_due_cards(cards, concept_map, config.scheduler)
        card = due[0] if due else None
        return TEMPLATES.TemplateResponse(
            request,
            "review.html",
            {"card": card, "remaining": len(due)},
        )

    @app.post("/review", response_class=HTMLResponse)
    async def review_submit(
        request: Request,
        card_id: int = Form(...),
        grade: int = Form(...),
    ):
        r = repo()
        graph, concept_map = load_graph()
        row = r.conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if not row:
            return RedirectResponse("/review", status_code=303)
        card = dict(row)
        concept = concept_map.get(card["concept_id"], {})
        state = SM2State(
            interval_days=float(card["interval_days"]),
            repetitions=int(card["repetitions"]),
            easiness=float(card["easiness"]),
        )
        new_state, next_due, boosts = apply_review(
            state,
            grade,
            graph,
            card["concept_id"],
            float(concept.get("centrality", 0)),
            config.scheduler,
        )
        r.update_card_sm2(
            card_id,
            new_state.interval_days,
            new_state.repetitions,
            new_state.easiness,
            next_due.isoformat(),
        )
        r.record_review(card_id, grade)
        for desc_id, boost in boosts:
            r.add_priority_boost(desc_id, boost)
        return RedirectResponse("/review", status_code=303)

    return app
