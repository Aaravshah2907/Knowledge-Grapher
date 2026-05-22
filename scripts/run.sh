#!/usr/bin/env bash
# Full pipeline: scan notes -> generate cards -> start local web UI.
# Prerequisite: ./scripts/setup.sh /path/to/notes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Error: .venv not found. Run ./scripts/setup.sh /path/to/notes first." >&2
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

run_kg() {
  if command -v kgrapher &>/dev/null; then
    kgrapher "$@"
  else
    python3 -m kgrapher "$@"
  fi
}

if [[ ! -f "$HOME/.kgrapher/config.yaml" ]]; then
  echo "Error: ~/.kgrapher/config.yaml not found. Run ./scripts/setup.sh /path/to/notes first." >&2
  exit 1
fi

echo "==> Scanning notes and rebuilding knowledge graph"
run_kg scan

echo "==> Generating draft flashcards"
run_kg cards generate

echo "==> Starting local web UI at http://127.0.0.1:8765 (Ctrl+C to stop)"
run_kg serve
