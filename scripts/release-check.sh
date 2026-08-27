#!/usr/bin/env bash
# Pre-push sanity check for Fedora (or any Linux box with PySide6).
set -euo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "==> $PYTHON --version"
"$PYTHON" --version

echo "==> unit tests"
"$PYTHON" -m unittest discover -s tests -v

echo "==> --version"
"$PYTHON" "$ROOT/pipes.py" --version

echo "==> --dump-screens"
"$PYTHON" "$ROOT/pipes.py" --dump-screens

echo "OK  ready to commit / tag (see docs/publishing.md)"
