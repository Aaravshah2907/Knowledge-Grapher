#!/usr/bin/env bash
# One-time setup: create venv, install deps, initialize kgrapher with your notes folder.
# Usage: ./scripts/setup.sh /path/to/markdown/notes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/markdown/notes" >&2
  echo "Example: $0 ~/Documents/my-vault" >&2
  exit 1
fi

if [[ ! -d "$1" ]]; then
  echo "Error: notes folder does not exist: $1" >&2
  exit 1
fi

NOTES_DIR="$(cd "$1" && pwd)"

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is required but not found on PATH" >&2
  exit 1
fi

cd "$ROOT"

echo "==> Creating virtual environment in $ROOT/.venv"
python3 -m venv .venv

# shellcheck source=/dev/null
source .venv/bin/activate

echo "==> Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

run_kg() {
  if command -v kgrapher &>/dev/null; then
    kgrapher "$@"
  else
    python3 -m kgrapher "$@"
  fi
}

echo "==> Initializing kgrapher with notes: $NOTES_DIR"
run_kg init "$NOTES_DIR"

echo ""
echo "Setup complete."
echo "  Notes vault: $NOTES_DIR"
echo "  Config:      $HOME/.kgrapher/config.yaml"
echo "  Database:    $HOME/.kgrapher/kgrapher.db"
echo ""
echo "Run the full pipeline:  ./scripts/run.sh"
