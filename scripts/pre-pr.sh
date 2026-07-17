#!/usr/bin/env bash
# Runs the same checks as CI, locally, without Docker.
# Requires: backend/.venv with `pip install -r requirements.txt -r requirements-dev.txt`,
# and frontend/node_modules from `npm install`.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."

make lint-backend
make test-backend

echo "==> frontend lint"
npm --prefix frontend run lint
echo "==> frontend type-check"
npm --prefix frontend run type-check
echo "==> frontend tests"
npm --prefix frontend test

echo "All checks passed."
