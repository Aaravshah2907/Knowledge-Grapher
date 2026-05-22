# Knowledge Grapher

A **local** tool for exam preparation in dense quantitative fields. It parses your Markdown notes (Obsidian-style), builds a **dependency knowledge graph**, runs **centrality-weighted spaced repetition** (SM-2 + PageRank cascade), and highlights **weak links** in your understanding.

No cloud, no account — your notes and review history stay on your machine.

## Who it's for

Students studying subjects like stochastic calculus, advanced physics, or any field where:

- Notes fragment across many files
- Concepts depend on each other in non-obvious ways
- Missing a foundational idea should raise urgency on everything downstream

## Quick start

### Install

```bash
git clone https://github.com/yourusername/Knowledge-Grapher.git
cd Knowledge-Grapher
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Initialize

Point the tool at your Markdown vault:

```bash
kgrapher init /path/to/your/notes
```

Or try the bundled example corpus:

```bash
kgrapher init examples/sample-notes
```

### Workflow

```bash
kgrapher scan              # Parse notes, build graph, compute PageRank
kgrapher cards generate    # Draft flashcards from titles + LaTeX
kgrapher review            # Interactive recall session
kgrapher weak              # Weak-link report
kgrapher graph export -o my-graph.html
kgrapher serve             # Local web UI at http://127.0.0.1:8765
```

## Authoring notes

Each `.md` file is one **concept**. Default id = filename (e.g. `ito-lemma.md` → `ito-lemma`).

```yaml
---
id: ito-lemma
title: Itô's Lemma
tags: [stochastic-calculus, sde]
aliases: [Ito lemma]
depends_on: [brownian-motion, stochastic-integral]
---
# Itô's Lemma

Relates to [[brownian-motion]] and [[stochastic-integral]].

$$dX_t = \mu_t\,dt + \sigma_t\,dW_t$$
```

| Source | Edge type | Used for |
|--------|-----------|----------|
| `depends_on` / `requires` in frontmatter | **Hard** dependency | PageRank, cascade on miss |
| `[[wikilink]]` in body | **Soft** link | Graph visualization |

**Edge direction:** `A → B` means *B depends on A*. If you miss a flashcard for a high-centrality concept, priority boosts cascade to all **hard** downstream concepts.

## How scheduling works

### SM-2

Standard SuperMemo SM-2 intervals and easiness (grades 0–5). Grade &lt; 3 counts as a **lapse** (interval resets).

### PageRank priority

Due-card priority:

```
priority = overdue_urgency × (1 + α × PageRank) + priority_boost
```

- `α` — centrality weight (default `1.0`)
- `β` — cascade boost on lapse (default `0.5`)

When you lapse on concept `n`, every hard downstream concept `d` receives:

```
priority_boost[d] += β × PageRank[n]
```

### Weak links

Concepts with **rolling accuracy &lt; 60%** (last N reviews, default N=7) and high centrality or prerequisites that unlock many topics.

## Configuration

Config file: `~/.kgrapher/config.yaml`

```yaml
notes_path: /path/to/notes
db_path: ~/.kgrapher/kgrapher.db
scheduler:
  alpha: 1.0
  beta: 0.5
  weak_window: 7
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

See [LOGBOOK.md](LOGBOOK.md) for a dated development log. Make one focused git commit per feature milestone.

## Roadmap

- [ ] PyPI publish (`pip install kgrapher`)
- [ ] Anki import/export
- [ ] Incremental scan (mtime/hash)
- [ ] PDF / LaTeX note sources

## License

MIT
