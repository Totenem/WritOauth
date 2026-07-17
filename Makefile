.PHONY: up down build migrate lint-backend fix-backend lint-frontend test-backend test-frontend check logs prune prune-all

# backend/.venv layout differs by OS: Scripts/ on Windows, bin/ elsewhere.
ifeq ($(OS),Windows_NT)
BACKEND_PY := .venv/Scripts/python.exe
# Force Git Bash for recipes. Without this, make falls back to cmd.exe when
# invoked from PowerShell/cmd (no SHELL env var set there) but uses real bash
# when invoked from a Git Bash session (which does set SHELL) — cmd wants
# backslash paths, bash wants forward slashes, so recipes can't satisfy both.
# Pinning SHELL makes recipe behavior consistent regardless of caller.
SHELL := C:/PROGRA~1/Git/bin/bash.exe
.SHELLFLAGS := -ec
else
BACKEND_PY := .venv/bin/python
endif

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head

# Runs against backend/.venv (not Docker) — the backend container image only
# has runtime deps, not black/ruff/mypy. See backend/requirements-dev.txt.
lint-backend:
	cd backend && $(BACKEND_PY) -m black --check .
	cd backend && $(BACKEND_PY) -m ruff check .
	cd backend && $(BACKEND_PY) -m mypy . --ignore-missing-imports

# Auto-fixes what lint-backend can fix (formatting + import order); mypy findings
# still need manual fixes, so run lint-backend after to see what's left.
fix-backend:
	cd backend && $(BACKEND_PY) -m black .
	cd backend && $(BACKEND_PY) -m ruff check . --fix

lint-frontend:
	docker compose exec frontend npm run lint
	docker compose exec frontend npm run type-check

test-backend:
	cd backend && $(BACKEND_PY) -m pytest tests/ -v

test-frontend:
	docker compose exec frontend npm test

# Runs the same checks as CI (black/ruff/mypy/pytest + frontend lint/type-check/test)
# against your local backend/.venv and frontend/node_modules — no Docker containers
# required. Run this before opening a PR. See scripts/pre-pr.sh.
check:
	bash scripts/pre-pr.sh

logs:
	docker compose logs -f

# Reclaim disk space safely: stops containers and drops dangling images +
# build cache. Named volumes (mysql_data, chroma_data, ollama_models) are KEPT,
# so your DB, vector store, and pulled models survive. Note the next build
# rebuilds from scratch (slower) since the cache is gone.
prune:
	docker compose down
	docker builder prune -f
	docker image prune -f

# Destructive full reset: also removes named volumes (wipes DB / vector store /
# Ollama models) and every unused image on the machine. Use only for a clean slate.
prune-all:
	docker compose down -v
	docker system prune -af --volumes
