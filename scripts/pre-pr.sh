#!/usr/bin/env bash
# Runs the same checks as CI, locally, without Docker.
# Requires: backend/.venv with `pip install -r requirements.txt -r requirements-dev.txt`,
# and frontend/node_modules from `npm install`.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ -x backend/.venv/Scripts/python.exe ]; then
    PY=backend/.venv/Scripts/python.exe
elif [ -x backend/.venv/bin/python ]; then
    PY=backend/.venv/bin/python
else
    echo "backend/.venv not found. Run: cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt" >&2
    exit 1
fi

echo "==> black"
"$PY" -m black --check backend
echo "==> ruff"
"$PY" -m ruff check backend
echo "==> mypy"
"$PY" -m mypy backend --ignore-missing-imports
echo "==> pytest"
"$PY" -m pytest backend/tests -v

echo "==> frontend lint"
npm --prefix frontend run lint
echo "==> frontend type-check"
npm --prefix frontend run type-check
echo "==> frontend tests"
npm --prefix frontend test

echo "All checks passed."
