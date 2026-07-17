# Local Development Setup

## Prerequisites

Install these before starting:

- **Docker Desktop** — [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop)
- **Node.js 20** — [nodejs.org](https://nodejs.org) or via `nvm`
- **Python 3.11** — [python.org](https://python.org) or via `pyenv`

## Environment Variables

Copy the template and fill in values:

```bash
cp .env.example .env
```

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `mysql+pymysql://writoauth:password@mysql:3306/writoauth_db` | MySQL connection string |
| `JWT_SECRET_KEY` | *(change this)* | Sign JWT tokens — use a long random string in prod |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `CHROMA_DB_PATH` | `/app/data/chromadb` | Where ChromaDB stores vector data |
| `HF_MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | LLM model name served by Ollama |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Sentence transformer for embeddings |
| `TOP_K` | `3` | Number of baseline samples retrieved per analysis |
| `MAX_CONTEXT` | `4096` | Maximum token context for LLM |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Used by the browser to reach the backend |
| `MYSQL_ROOT_PASSWORD` | `rootpassword` | MySQL root password (Docker only) |
| `MYSQL_DATABASE` | `writoauth_db` | Database name |
| `MYSQL_USER` | `writoauth` | Application DB user |
| `MYSQL_PASSWORD` | `password` | Application DB password |

**Note on `NEXT_PUBLIC_API_URL`:** When the browser makes requests, it must use `http://localhost:8000`. When the frontend container talks to the backend container, it uses `http://backend:8000`. These are different — the `docker-compose.yml` sets `NEXT_PUBLIC_API_URL=http://localhost:8000` as a container override, which is correct for a dev setup where the browser accesses the backend through the host.

## Docker Services

```
docker compose up
```

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js dev server |
| `backend` | 8000 | FastAPI with hot reload |
| `mysql` | 3306 | MySQL 8.0 — application database |
| `chromadb` | 8001 | ChromaDB — vector store for embeddings |
| `ollama` | 11434 | Ollama — serves the Qwen LLM |

Start only infrastructure (for local code development):

```bash
docker compose up mysql chromadb ollama
```

## Running Database Migrations

After pulling changes that include new migrations:

```bash
make migrate
# or directly:
docker compose exec backend alembic upgrade head
```

To create a new migration after changing a SQLAlchemy model:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe your change"
```

Then review the generated file in `backend/database/migrations/versions/` before committing it.

## First-Time Ollama Model Setup

Ollama needs to download the model before the AI pipeline works:

```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
```

This is a one-time step per machine. The model is cached in the `ollama_models` Docker volume.
