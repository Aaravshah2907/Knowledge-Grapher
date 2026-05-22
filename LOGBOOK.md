# Development Logbook

Dated log of changes. One git commit per major feature where noted.

## 2026-05-22 — Project scaffold

- Added `pyproject.toml` with hatchling build and `kgrapher` CLI entry point
- Package layout under `src/kgrapher/`
- Config (`~/.kgrapher/config.yaml`), SQLite schema, `kgrapher init`
- README and LOGBOOK skeleton
- Commit: `chore: initial project scaffold`

## 2026-05-22 — Parser

- Markdown scanner with YAML frontmatter (`python-frontmatter`)
- Obsidian `[[wikilinks]]` and `depends_on` / `requires` extraction
- LaTeX formula extractor (`$...$`, `$$...$$`, equation environments)
- Parser unit tests with fixture notes
- Commit: `feat(parser): markdown graph extraction`

## 2026-05-22 — Graph and centrality

- NetworkX directed graph builder (hard/soft edges)
- PageRank on hard-dependency subgraph
- `kgrapher scan` persists concepts, edges, centralities
- `kgrapher graph export` HTML via pyvis
- Commit: `feat(graph): build dependency graph and PageRank`

## 2026-05-22 — Spaced repetition

- SM-2 implementation with lapse detection
- Centrality-weighted due queue
- Cascade priority boost on downstream concepts after miss
- `kgrapher review` interactive CLI session
- Commit: `feat(srs): SM-2 with centrality cascade`

## 2026-05-22 — Weak links and polish

- `kgrapher weak` report (rolling accuracy + centrality)
- `kgrapher cards generate` from titles and LaTeX
- `examples/sample-notes` stochastic calculus demo vault
- Integration tests and complete README
- Commit: `feat: weak-link analysis and documentation`

## 2026-05-22 — Web UI

- FastAPI local app: dashboard, scan, review, weak links, graph viewer
- `kgrapher serve` binds `127.0.0.1` only (offline-first)
- Commit: `feat(web): local review and graph viewer`
