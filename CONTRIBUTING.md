# Contributing to WritOauth

WritOauth is an AI-powered authorship verification platform that helps educators verify student writing authenticity. This guide gets you from zero to a running development environment.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | Latest | Runs all services (MySQL, ChromaDB, Ollama) |
| Node.js | 20+ | Frontend development outside Docker |
| Python | 3.11+ | Backend development outside Docker |
| Git | Any | Version control |

## Quick Start (3 commands)

```bash
git clone <repo-url> && cd WritOauth
cp .env.example .env
docker compose up
```

After the containers start:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- ChromaDB: http://localhost:8001
- Ollama: http://localhost:11434

## Running Without Docker (Faster Dev Loop)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # fill in local values
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

You still need MySQL, ChromaDB, and Ollama running. The easiest way is to start only those services via Docker:

```bash
docker compose up mysql chromadb ollama
```

## Branch Naming (Git Flow Lite)

```
main          ← production (protected, auto-deploys)
develop       ← integration (PRs merge here first)
feature/xyz   ← new features
fix/xyz       ← bug fixes
chore/xyz     ← tooling, docs, deps
```

Always branch off `develop`, not `main`.

## Pull Request Process

1. Branch off `develop`: `git checkout -b feature/your-feature develop`
2. Write code and tests
3. Ensure CI passes locally:
   ```bash
   make lint-backend   # black + ruff + mypy
   make test-backend   # pytest
   make lint-frontend  # eslint + tsc
   make test-frontend  # vitest
   ```
4. Open PR targeting `develop`
5. Request review — `@Totenem` is automatically assigned via CODEOWNERS

## Project Docs

Detailed architecture documentation lives in [`docs/`](docs/). For developer-specific guides, see [`docs/development/`](docs/development/).
