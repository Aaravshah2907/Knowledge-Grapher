# Knowledge Grapher

A **local** tool for exam preparation in dense quantitative fields. It parses your Markdown notes (Obsidian-style), builds a **dependency knowledge graph**, runs **centrality-weighted spaced repetition** (SM-2 + PageRank cascade), and highlights **weak links** in your understanding.

No cloud, no account — your notes and review history stay on your machine.

## Who it's for

Students studying subjects like stochastic calculus, advanced physics, or any field where:

- Notes fragment across many files
- Concepts depend on each other in non-obvious ways
- Missing a foundational idea should raise urgency on everything downstream

## Quick start

### Shell scripts (recommended)

```bash
git clone https://github.com/yourusername/Knowledge-Grapher.git
cd Knowledge-Grapher
chmod +x scripts/setup.sh scripts/run.sh

# One-time setup — pass your markdown notes folder
./scripts/setup.sh /path/to/your/notes
# Example with bundled demo notes:
./scripts/setup.sh examples/sample-notes

# Scan → generate cards → start web UI
./scripts/run.sh
```

### Manual install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
kgrapher version            # should print: kgrapher 0.1.0
```

If you see `kgrapher: command not found`, activate `.venv` or use:

```bash
.venv/bin/kgrapher version
python3 -m kgrapher version
```

### CLI workflow

```bash
kgrapher init /path/to/your/notes
kgrapher scan
kgrapher cards generate
kgrapher review
kgrapher weak
kgrapher graph export          # writes ~/.kgrapher/graph-export.html by default
kgrapher serve                 # http://127.0.0.1:8765
```

Generated artifacts (`lib/`, `*-graph.html`, `.venv`, `~/.kgrapher/`) are gitignored and never committed.

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

### Flashcard formula (optional)

`kgrapher cards generate` picks the **card back** in this order:

1. **`card_formula`** (or `key_formula`) in frontmatter — use this when you want a specific identity on the card
2. Otherwise the **first `$$...$$` display equation** in the note body (in top-to-bottom order)
3. Then any **`$...$` inline** math, if there are no display blocks
4. If there is no math, `See note: <filename>`

You do **not** need to reorder your whole note for a setup line like `$X_t$` before the main `$$` result — put the main result in the first `$$` block, or set `card_formula` explicitly:

```yaml
card_formula: "df(t,X_t) = \\frac{\\partial f}{\\partial t}\\,dt + \\cdots"
```

Regenerate after edits: `kgrapher cards generate --overwrite`

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
